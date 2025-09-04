from pathlib import Path
import slideinfo
import subprocess
import argparse
import re
import shutil

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


# 文字列位置を取得
def find_frame_positions(s):
###    pattern = r'\\begin{frame}.*?\\end{frame}'
    # 正規表現で \begin{frame} 〜 \end{frame} を含むブロック + 直後の改行も含める
    pattern = r'(\\begin{frame}.*?\\end{frame})(\n|$)'
    matches = list(re.finditer(pattern, s, flags=re.DOTALL))
    return [(m.start(), m.end()) for m in matches]

def themechk(fs):
    # 正規表現で抽出
    # 行の中からパターンを探す
    match = re.search(r"@@@--\((.*?)\)--@@@", fs)
    if match:
        extracted = match.group(1)  # ( ... ) 内の文字列
        if extracted in ["metropolis","SimpleDarkBlue"]:
            return extracted
        else:
            print(f'テーマの値が不正です {extracted}')
            exit(1)
    else:
        #マッチしない時は"SimpleDarkBlue"を返す
        return "SimpleDarkBlue"

# --------------------------------------------------------------------------
ws=slideinfo.slidetitle(subj_code, tdir_name)

# contentファイルの読み込み
# 1. content.tex　をターゲットディレクトリよりコピー
buld_slide = Path(__file__).parent
tagdir = slideinfo.slidedir(subj_code, tdir_name)
fromPath = buld_slide.parent/tagdir/'content.tex'
with open(fromPath, encoding="utf-8") as f:
    text2 = f.read()

# 2. 作成するpdfのファイル名を作成
output_pdf_name = tdir_name+'_'+ws + ".pdf"
print('pdfname:',output_pdf_name)

# 2.1 content.texの１行目にthemeの指定があるかチェック
ctheme=themechk((text2.splitlines())[0])
print(f"beamerテーマ: {ctheme}")

print(buld_slide.parent/tagdir)

tempdic={"SimpleDarkBlue":"main_template_org.txt", "metropolis":"metro_template_org.txt"}

# 3. main_temp.texの生成　imagesディレクトリをターゲットディレクトリ名にする(footerにディレクトリ表示をする）
replacements = {
    "@@sdir@@": tagdir,
    "@@stitle@@": tdir_name+' '+ws
}

# テンプレートファイルのあるディレクトリ
with open(buld_slide / 'templates' / tempdic[ctheme], encoding='utf-8') as f:
    text = f.read()

for key, value in replacements.items():
    text = text.replace(key, value)

if outflg:
    pause_setting = r"\mypausemodefalse"
else:
    pause_setting = r"\mypausemodetrue"
text = text.replace("%@@pausemode@@", pause_setting)

if techflg:
    pause_setting = r"\teachermodetrue"
else:
    pause_setting = r"\teachermodefalse"
text = text.replace("%@@teachermode@@", pause_setting)

# main.texを生成する
with open("main.tex", "w", encoding="utf-8") as f:
    f.write(text)
    f.write("\n")
    f.write(text2)
    f.write(r"\end{document}")

#--main.texのコピー---------------------------------------
shutil.copy("main.tex", buld_slide.parent/tagdir/"main.tex")
print("main.texをコピーしました")

#テーマ別の実行用のリストを辞書化
rundic={"SimpleDarkBlue":["lualatex", "-interaction=nonstopmode", "main.tex"], 
        "metropolis":["latexmk", "-lualatex", "-shell-escape","-interaction=nonstopmode", "-file-line-error", "main.tex"]}

for i in range(2):
    result =  subprocess.run(
    rundic[ctheme],  #　テーマによって実行されるパラメータが違う
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
output_pdf_name=Path(output_pdf_name)
if fp > 0:
    output_pdf_name = output_pdf_name.with_name(output_pdf_name.stem + "_test" + output_pdf_name.suffix)
else:  #プレゼン資料
    if techflg:  #  教師フラッグがON
        output_pdf_name = output_pdf_name.with_name(output_pdf_name.stem + "_tech" + output_pdf_name.suffix)
    elif not outflg:  # ハンズアウトフラッグがOFF
        output_pdf_name = output_pdf_name.with_name(output_pdf_name.stem + "_pr" + output_pdf_name.suffix)

#--------------------------------------------

toPath = buld_slide.parent/tagdir/output_pdf_name
# ファイル名の直前に '_test' を追加
pdf_path = buld_slide / "main.pdf"
shutil.copy(pdf_path, toPath)
print('PDF名: ',output_pdf_name)

# 7. 中間ファイル、生成ファイルの削除
for ext in [".aux", ".log", ".nav", ".out", ".snm", ".toc", ".vrb", ".pdf", ".tex","_temp.tex"]:
    try:
        (buld_slide / f"main{ext}").unlink()
    except FileNotFoundError:
        pass
#(buld_slide / "content.tex").unlink()

# 8. slideinfoのアップデート
slideinfo.slideinfoupdate(args.items[0],args.items[1])