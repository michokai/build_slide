from datetime import datetime
from pathlib import Path
import json

build_slide = Path(__file__).parent
def readslidejson():
    filename = build_slide / "slideinfo.json"

    with open(filename, 'r', encoding='utf-8') as f:
        # json.load() を使ってファイルオブジェクトから直接辞書を読み込む
        sdic = json.load(f)
    return sdic

def outputslidejson(sdic):
    # ファイルを開いて辞書をJSON形式で書き出す
    # 'w' モードでファイルを開く（ファイルが存在しない場合は新規作成、存在する場合は上書き）
    filename = build_slide / "slideinfo.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(sdic, f, ensure_ascii=False, indent=4)

def slidedir(subject,course):
    sdic = readslidejson()
    # 1. subject の存在チェック
    try:
        _ = sdic[subject] # 値は必要ないが、アクセスを試みる
        return f"{sdic[subject]['dir']}/{course}"
    except KeyError:
        print(f'** ({subject}) は存在しません **')
        return None

def slidetitle(subject,course):
    sdic = readslidejson()
    # 1. subject の存在チェック
    try:
        _ = sdic.get(subject) # 値は必要ないが、アクセスを試みる
        return sdic[subject][course]['title']
    except KeyError:
        print(f'** ({subject}) にtitleが存在しません **')
        return 'unknownTitle'

def slideinfoupdate(subject,course):
    sdic = readslidejson()
    dt=datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if subject not in sdic:
        raise KeyError(f"Key '{subject}' not found in slideinfo.json")   
    if course not in sdic[subject]:
        raise KeyError(f"course Key '{course}' not found in slideinfo.json")
    
    if sdic[subject][course]['count']>0:
        sdic[subject][course]['update_at']=dt
    else:
        sdic[subject][course]['created_at']=dt
    sdic[subject][course]['count']+=1
    
    # ファイルを開いて辞書をJSON形式で書き出す
    outputslidejson(sdic)

def slide_getdir(subject):
    sdic = readslidejson()
    return sdic[subject]['dir']


if __name__ == '__main__':
    wdir=slidedir('1020801','04')
    if not wdir:
        print('error')
    else:
        print(wdir)

    print(slidetitle('1020801','05'))