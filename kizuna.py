#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import fileinput
import re
import sys
import subprocess
import datetime

#
# Settings
#
weekday_jp = ["月","火","水","木","金","土","日"]
ThisYear = datetime.date.today().year

#
# arguments
#
parser = argparse.ArgumentParser(prog="kizuna.py", description="kizuna record formatter")
parser.add_argument('files', metavar='FILE', nargs='*', help='files to read, if empty, stdin is used')
parser.add_argument('-e', '--event', action='store_true', help='Event scoring mode')
parser.add_argument('-wld', '--winlosedraw', metavar='N,N,N,N,N,N,N,N,N,N,N,N', default='0,0,0,0,0,0,0,0,0,0,0,0',
                 help='Counts of Win,Lose,Draw for each army. ex) -wld 2,6,0,25,21,4,11,8,1,8,10,0')
parser.add_argument('-d', '--debug', action='store_true', help='Print filename and line no')
args = parser.parse_args()

#
# Win/Lose/Draw class
#
class WLD:
        def __init__(self, win=0, lose=0, draw=0):
                self.win  = win
                self.lose = lose
                self.draw = draw
                self.history  = []

        def set(self, win=0, lose=0, draw=0):
                self.win  = win
                self.lose = lose
                self.draw = draw

        def countup(self, strval, training):
                if training:
                        v = 0
                        h = "他"
                else:
                        try:
                                v = int(strval)
                        except ValueError:
                                v = -1
                                print('Error: WLD:countup illegal input value = "{}"'.format(strval))
                        if v == 10:
                                h = "勝利"
                                self.win += 1
                        else:
                                if v == 5:
                                        h = "敗北"
                                        self.lose += 1
                                else:
                                        h = "分/CPU"
                                        self.draw += 1
                self.history.append(h)
                return h

        def total(self):
                return self.win+self.lose+self.draw

        def sprint(self, msgtype=0):
                if(msgtype == 1):
                        return "{}勝{}敗{}他".format(self.win, self.lose, self.draw)
                elif(msgtype == 2):
                        t = self.win + self.lose + self.draw
                        r = int(self.win / t * 100) if t != 0 else 0
                        return "{:3d}戦{:3d}勝{:3d}敗{:3d}分/CPU (勝率{}%)".format(self.total(), self.win, self.lose, self.draw, r)
                else:
                        return "{},{},{}".format(self.win, self.lose, self.draw)

        def sprint_history(self):
                return self.history

#
# Methods
#
def army(m):
        if(re.search(r"白ザク", m)):
                return("連邦")
        elif(re.search(r"ザク|ドム|ゲル|白タン|ヅダ|マリーネ|ドライセン|イフ", m)):
                return("ジオン")
        elif(re.search(r"ジム|ダム|ガン|犬|元|量|スト|タン|豆腐|ハイブー|ユニ|FAB|ジェ|ガーカス|駒|窓|ブル|キャ|Z|ピクシー|デルタ|百|夜鹿|ジ・O|メタスパ|BD|ボール|ネモ|バンシィ|簡八|ディアス", m)):
                return("連邦")
        else:
                return("ジオン")

def stage_str(s):
        s0 = str(s)
        s1 = "サイド"+s0 if re.match(r"\d", s0) else s0
        return re.sub(r'[rR]$', '(R)', s1)

def print_battle_record(nr, event_a, mcard, wld_0f, wld_0z, wld_1f, wld_1z, l, debug_a):
        game0  = l[0] # ex) 88 or CPU44 or トレモ44拠点 or p44
        stage0 = l[1] # ex) NY
        ms0    = l[2] # ex) マカク
        win0   = l[3] # ex) 10
        base0  = l[4] # ex) 6
        game1  = l[5] # ex) 66 or CPU44 or トレモ44MS戦
        stage1 = l[6] # ex) リボB
        ms1    = l[7] # ex) マカク
        win1   = l[8] # ex) 5
        base1  = l[9] # ex) 3
        if(event_a and len(l) == 12):
                gauge  = l[10] # ex) 24
                gtotal = l[11] # ex) 456
        else:
                gauge  = -1
                gtotal = -1
        
        if(debug_a):
            j = 0
            for fld in l:
                print("\t{0}\t{1}".format(j, fld))
                j += 1

        a = army(ms0)
        wld = (wld_0f if(a == '連邦') else wld_0z) if mcard else (wld_1f if(a == '連邦') else wld_1z)
        s0 = stage_str(stage0)
        tr0 = True if (re.search(r'トレモ', game0) or re.match(r'p', game0)) else False
        w0 = wld.countup(win0, tr0)
        s1 = stage_str(stage1)
        game1a = game0 if re.search(r'同', game1) else game1
        tr1 = True if(re.search(r'トレモ', game1a) or re.match(r'p', game0)) else False
        w1 = wld.countup(win1, tr1)
        print("{0:2d})".format(nr), end="")
        w0p = "" if tr0 else "→ {}".format(w0)
        w1p = "" if tr1 else "→ {}".format(w1)
        if(mcard):
                print("①", end="")
        else:
                print("②", end="")
        print(" {0} {1} {2}@{3}{4}, {5} {6}@{7}{8}".format(a, game0, ms0, s0, w0p, game1, ms1, s1, w1p), end="")
        if(event_a and ((not tr0) or (not tr1))):
                print(" +{0}/{1} {2}".format(gauge, gtotal, wld.sprint(1)))
        else:
                print("");

def print_others(line):
        if re.match(r"^\s*#", line):
                line = re.sub(r"^\s*","",line)
                print(line, end="\n")
        elif re.match(r"^\s+", line):
                        print("　　　  {}".format(line))
        elif not re.match(r"^\s*$", line):
                if re.match(r"連邦優勢", line) or re.match(r"ジオン優勢", line):
                        print("{}".format(line))
                else:
                        print("  メモ: {}".format(line))

def print_date(m):
        month = int(m.group(1))
        day   = int(m.group(2))
        ymd = datetime.datetime(ThisYear,month,day)
        print("\n●  {}/{}({})".format(month,day,weekday_jp[ymd.weekday()]))

def print_event_summary(wld_0f, wld_0z, wld_1f, wld_1z):
        print("")
        print("連邦①  {}".format(wld_0f.sprint(2)))
        print("Zeon①  {}".format(wld_0z.sprint(2)))
        print("連邦②　{}".format(wld_1f.sprint(2)))
        print("Zeon②　{}".format(wld_1z.sprint(2)))
        fh = open("kizuna_pragma_tmp.txt", "w")
        fh.write("# pragma event\n")
        fh.write("# pragma wld {},{},{},{}\n".format(wld_0f.sprint(),wld_0z.sprint(),wld_1f.sprint(),wld_1z.sprint()))
        fh.close()

#
#        Main routine
#
def main():
        # Setup from arguments - Debug output
        debug_a = args.debug
        event_a = args.event

        # Win, Lose, Draw of Federation and Zeon
        (w0f, l0f, d0f, w0z, l0z, d0z, w1f, l1f, d1f, w1z, l1z, d1z) = list(map(int, args.winlosedraw.split(',')))

        pragma_on = True
        wld_0f = WLD(w0f,l0f,d0f)
        wld_0z = WLD(w0z,l0z,d0z)
        wld_1f = WLD(w1f,l1f,d1f)
        wld_1z = WLD(w1z,l1z,d1z)
        nl = 0  # number of input lines
        nr = 0  # number of record data lines
        for line in fileinput.input(files=args.files,openhook=fileinput.hook_compressed):
                nl += 1
                if(debug_a): print("[{:4d}]\t{}".format(nl,line),end="")

                # 
                # pragma handling
                # 
                m = re.match(r"^#\s*pragma\s+(.*)$", line)
                if(m):
                        if(pragma_on):
                                pragma_cmd = m.group(1)
                                if re.match(r"event", pragma_cmd):
                                        event_a = True
                                elif re.match(r"wld", pragma_cmd):
                                        m = re.match(r"wld\s+(\S+)$", pragma_cmd)
                                        wld_val = m.group(1)
                                        (w0f, l0f, d0f, w0z, l0z, d0z, w1f, l1f, d1f, w1z, l1z, d1z) = list(map(int, wld_val.split(',')))
                                        wld_0f.set(w0f,l0f,d0f)
                                        wld_0z.set(w0z,l0z,d0z)
                                        wld_1f.set(w1f,l1f,d1f)
                                        wld_1z.set(w1z,l1z,d1z)
                        continue
        
                if not re.match(r"^\s+", line):
                        pragma_on = False

                # 
                # Battle record handling
                # 
                line = line.rstrip("\r\n")
                mcard = False if re.match(r"^\s*サブ\s*", line) else True
                if not mcard: line = re.sub(r"^\s*サブ\s*", "", line, 1)
        
                line = re.sub(r"トレモ\s*","トレモ",line)
                line = re.sub(r"^p\s*","p",line)        # private match
                l0 = line.replace("、"," ")
                l = l0.split()
        
                if((event_a and len(l) == 12) or ((not event_a) and len(l) >= 10)):
                    nr += 1
                    print_battle_record(nr, event_a, mcard, wld_0f, wld_0z, wld_1f, wld_1z, l, debug_a)
                else:
                    m = re.match(r"\s*(\d+)/(\d+)\s*$", line)
                    if(m):
                        print_date(m)
                    else:
                        print_others(line)
        
        if(event_a):
                print_event_summary(wld_0f, wld_0z, wld_1f, wld_1z)


if __name__=="__main__":
        main()

