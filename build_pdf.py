import subprocess
from pathlib import Path
import re
import shutil
import re
import argparse
import slideinfo

def parse_page_range(range_str: str) -> tuple[int, int]:
    """ページ範囲の文字列を解析して (fp, tp) を返す。無効なら (-1, -1)。"""
    if not range_str:
        return -1, -1  # 引数なしの場合

    if "-" in range_str:
        try:
            start, end = map(int, range_str.split("-"))
            if start==0:
                start=1
            if start > end:
                end=start
            return start, end
        except ValueError:
            raise argparse.ArgumentTypeError("ページ範囲は整数で '開始-終了' の形式で指定してください")
    else:
        try:
            page = int(range_str)
            if page==0:
                return 1, 1
            return page, page
        except ValueError:
            raise argparse.ArgumentTypeError("ページ範囲は整数で指定してください")

# ✅ 引数の設定
parser = argparse.ArgumentParser()

# 必須の2つの位置引数（科目コードとディレクトリ名）
parser.add_argument("items", nargs=2, help="必須の2つの引数（例: input1 input2）")

# オプション1：ページ範囲
parser.add_argument("--page", "-p", default="", help="出力ページ範囲（例: 5 または 3-7）")

# オプション2：ハンドアウトモード
# hoモード（任意、指定があればTrueになる）
parser.add_argument("--ho", action="store_true", help="ハンドアウトモードを有効にする")

# オプション3：生徒・教師モード
# techモード（任意、指定があればTrueになる）
parser.add_argument("--tech", action="store_true", help="教師モードを有効にする")  # ← 追加！

args = parser.parse_args()

# ✅ ディレクトリ構築
subj_code, tdir_name = args.items
tagdir = slideinfo.slidedir(subj_code, tdir_name)
if not tagdir:
    exit()

# ✅ ページ範囲の解析
try:
    fp, tp = parse_page_range(args.page)
except argparse.ArgumentTypeError as e:
    parser.error(str(e))

# ✅ handoutモード判定
# hoモード
outflg = args.ho

# ✅ techerモード判定
# techモード
techflg = args.tech

# ✅ 確認出力（または後続処理）
print(f"対象ディレクトリ: {tagdir}")
print(f"ページ範囲: {fp} ～ {tp}" if fp != -1 else "ページ範囲: 指定なし")
print(f"ハンドアウトモード: {outflg}")
print(f"生徒・先生モード: {techflg}")

# ----------------------------------------------------
def sanitize_filename(name: str) -> str:
    """
    macOSで使用できないファイル名文字を除去・置換し、
    近い安全なファイル名を返す。
    """
    # スペース（半角・全角）を削除
    name = name.replace(" ", "").replace("　", "")

    # 禁止文字（macOSでは : や / は使えない。/ はディレクトリ区切り）
    name = re.sub(r'[:/]', '_', name)

    # macOSで特殊扱いの "." や空文字列の処理
    name = name.strip(".")
    if not name:
        name = "default_filename"

    return name

def is_valid_filename_mac(name: str) -> bool:
    """
    macOSでの使用に対して安全なファイル名かを確認
    """
    if not name or name.strip(".") == "":
        return False
    if re.search(r'[:/]', name):
        return False
    return True

def replace_space_with_underscore(text):
    if '　' in text:  # 全角スペースが含まれている場合
        return re.sub('　+', '_', text)
    else:             # 半角スペースが含まれている場合（または混在していない）
        return re.sub(' +', '_', text)

# 文字列位置を取得
def find_frame_positions(s):
###    pattern = r'\\begin{frame}.*?\\end{frame}'
    # 正規表現で \begin{frame} 〜 \end{frame} を含むブロック + 直後の改行も含める
    pattern = r'(\\begin{frame}.*?\\end{frame})(\n|$)'
    matches = list(re.finditer(pattern, s, flags=re.DOTALL))
    return [(m.start(), m.end()) for m in matches]


buld_slide = Path(__file__).parent
print(buld_slide.parent/tagdir)

# 1. content.tex　をターゲットディレクトリよりコピー
fromPath = buld_slide.parent/tagdir/'content.tex'
shutil.copy(fromPath, buld_slide)

# 2. 作成するpdfのファイル名を作成
with open(buld_slide /'content.tex') as f:
    s = f.read()
mtit='title{'
wname=(replace_space_with_underscore(s[s.find(mtit)+6:s.find('}',s.find(mtit))]))
pdfname=sanitize_filename(wname)

# 3. main_temp.texの生成　imagesディレクトリをターゲットディレクトリ名にする(footerにディレクトリ表示をする）
with open(buld_slide / 'templates/main_template.tex', encoding='utf-8') as f_in, \
     open(buld_slide / 'main_temp.tex', 'w', encoding='utf-8') as f_out:
    f_out.write(f_in.read().replace('@@dir@@', tagdir).replace('@@footer@@', tagdir))  #.split('/')[0]

buld_slide = Path(__file__).parent
root_dir = buld_slide#.parent.parent
print(root_dir)
#exit()
template_dir = root_dir / "template"

main_tex = root_dir / "main.tex"
output_pdf_name = pdfname + ".pdf"
print(buld_slide.name)

# PDF作成が全ページか一部かの判定（fpが負の値なら全ページ)
# 引数のページ範囲がある場合はfp>0　デフォルトは全ページでfpの値は−１
if fp > 0:
    frame_ranges = find_frame_positions(s)
    print(len(frame_ranges))
    print(frame_ranges)
    # 引数の指定ページが最終ページより大きい場合は最終ページをセットする(fp,tp両方チェック)
    if fp > len(frame_ranges)-1:
        fp = len(frame_ranges)-1
    if tp > len(frame_ranges)-1:
        tp = len(frame_ranges)-1
    fpoint,tpoint=frame_ranges[fp-2][0] , frame_ranges[tp-2][1]
else:
    fpoint,tpoint = None,None
# 4. main_head.tex + content.tex + \end{document} を main.tex にまとめる
with open(main_tex, "w", encoding="utf-8") as out:
    out.write((root_dir / "main_temp.tex").read_text(encoding="utf-8"))
    if outflg:
        out.write("\mypausemodefalse % pauseを消す\n")  #ハンズアウト用
    else:
        out.write("\mypausemodetrue % pauseを残す\n")  #プレゼン資料
    if techflg:
        out.write("\\teachermodetrue % ← 教師用\n")
    else:
        out.write("\\teachermodefalse % ← 生徒用\n")
    if fp > 0:
        out.write("\\begin{document}\n")
    out.write(s[fpoint:tpoint])
#    out.write("\n\\input{content.tex}\n")
####    out.write("\\end{document}\n")  # ← ここだけファイルにせず直接書く

# 5. LaTeX コンパイル  main.pdfが生成される
for i in range(2):
    result = subprocess.run(
        ["lualatex", "-interaction=nonstopmode", "main.tex"],
        cwd=buld_slide,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("❌ LaTeX コンパイル失敗")
        print(result.stderr)
        exit(1)
    else:
        if i == 0:
            print("✅ LaTeX コンパイル成功")


pdf_path = buld_slide / "main.pdf"
if not pdf_path.exists():
    print("❌ LaTeX main.pdfが生成されていません")
    exit(1)

# 6. PDFをターゲットディレクトリにコピーする
if fp > 0:
    output_pdf_name=Path(output_pdf_name)
    output_pdf_name = output_pdf_name.with_name(output_pdf_name.stem + "_test" + output_pdf_name.suffix)
else:  #プレゼン資料
    if not outflg:
        output_pdf_name=Path(output_pdf_name)
        output_pdf_name = output_pdf_name.with_name(output_pdf_name.stem + "_pr" + output_pdf_name.suffix)

#--------------------------------------------
tomaintex=buld_slide.parent/tagdir/"main.tex"
shutil.copy(main_tex, tomaintex)

toPath = buld_slide.parent/tagdir/output_pdf_name
# ファイル名の直前に '_test' を追加

shutil.copy(pdf_path, toPath)

# 7. 中間ファイル、生成ファイルの削除
for ext in [".aux", ".log", ".nav", ".out", ".snm", ".toc", ".vrb", ".pdf", ".tex","_temp.tex"]:
    try:
        (buld_slide / f"main{ext}").unlink()
    except FileNotFoundError:
        pass
(buld_slide / "content.tex").unlink()

# 8. slideinfoのアップデート
slideinfo.slideinfoupdate(args.items[0],args.items[1])