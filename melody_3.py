import mido
import random
from mido import Message, MidiFile, MidiTrack

#毎回変える部分
seed = 2
#一小節一個のMIDI番号
stem = [] #メロディの幹．number_of_measure個のリスト. keyに合う音を入れる必要あり
key = 4 #キー．0~11の整数．Cが0
tempo =116; #テンポ
filename=f"A1_{seed}_melody.mid"
fileStem = "A1.mid"

random.seed(seed)
mid = MidiFile()
track = MidiTrack()
mid.tracks.append(track)
#一単位の時間を設定
unit = 480 # 4分音符を1単位とする
signature = 3 #拍子 ここ変える場合プログラムも変更する必要あり
pattern = [] #i+1小節目のパターン番号．4/4拍子の場合は事前に決めた0~4. 
note_order = [] #一小節内の音符の順番
order_bank = [] #音符のリスト.
note_bank = [[]] #音符のリスト. 
note_tone = [] #音程のリスト(上下を表す.)
tone_bank = []
melody = [] #最終的なメロディ
melody_bank = [] #メロディのリスト
rythm = [] #ドラムの強（中）弱のパターン. アクセントの位置を利用したい．ドラムパターンプログラムから持ってくるかも．
number_of_measure = 8 #一度に作る小節数
measure = 0 #今の小節数. measure+1小節目．
rate = 1 #音程の変化率．
temp = 0
sum = 0



trans_prob =[[]]; #パターンの推移確率行列
retain = 0
vel=90
adapt = [0, 0, 1, 0, 2, 3, 0, 4, 0, 5, 0, 6] #12音階を0~6の数字に変換
scale = [2, 2, 1, 2, 2, 2, 1] #メジャースケール
degree = [] #度数


#旋律の推移確率行列を設定. 
trans_prob =   [[0.2, 0.6, 0.2],
                [0.3, 0.5, 0.2],
                [0.4, 0.5, 0.1]]

note_bank =    [[3, 0, 0],
                [1, 2, 0],
                [1, 1, 1]] #pattern = 0~4の音符リスト. 数字は音符の長さを表す. 0は意味なし, 途中に入れてはいけない

#推移確率行列が正規化されているか確認
#for i in range(number_of_inst):
#    print(sum(trans_prob[i]))

#値とmidiのnote番号の対応を表すリスト
midinote = []

#テンポを設定
track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(tempo)))

#初期化メソッド
def init():
    for i in range(number_of_measure): #i=0~2
        pattern.append(0)
        order_bank.append([0, 0, 0])
        tone_bank.append([0, 0, 0]) #三拍子なので
        melody_bank.append([0, 0, 0])
    for i in range(signature):
        note_order.append(0)
        note_tone.append(0)
        melody.append(0)
        degree.append(0)

#midiファイルを読み込みstemに格納するメソッド
def read_midi():
    midStem = MidiFile(fileStem)
    trackStem = midStem.tracks[0]
    for msg in trackStem:
        if msg.type == 'note_on':
            stem.append(msg.note)

#patternを決めて返すメソッド
def update_pattern():
    for i in range(number_of_measure):
        if(i == 0):
            temp = random.random() 
            sum = 0
            for j in range(len(note_bank)):
                if(sum <= temp and temp < sum + trans_prob[0][j]):
                    pattern[i] = j
                    break
                else:
                    sum += trans_prob[0][j]
        else:
            temp = random.random()
            sum = 0
            for j in range(len(note_bank)):
                if(sum <= temp and temp < sum + trans_prob[pattern[i-1]][j]):
                    pattern[i] = j
                    break
                else:
                    sum += trans_prob[pattern[i-1]][j]
    return pattern

#note_orderを返すメソッド
def update_note_order(number_of_pattern): #pattern[i]に対応するnote_orderを返す
    note_order = note_bank[number_of_pattern] #仮. 0は途中にあってはいけない
    #note_orderの中身を並び替える
    random.shuffle(note_order) 
    #0の位置を後ろに移動
    for i in range(len(note_order)):
        for j in range(len(note_order)):
            if  j < len(note_order)-1 and note_order[j] == 0:
                note_order.append(note_order.pop(j))
                break
            elif j == len(note_order)-1:
                return note_order 
    return note_order

#note_toneを更新して返すメソッド
def update_note_tone(number_of_pattern):
    #note_toneの初期化
    note_tone = [0 for i in range(signature)] 
    for i in range(signature):
        if(i == 0):
            note_tone[i] = 0
        else:
            note_tone[i] = random.randint(-1, 1) #-1:下行, 0:同音, 1:上行 
    return note_tone
    
    
#音符の長さと音程を元にメロディを生成して返すメソッド
def update_melody(note_order, note_tone, measure, rate):
    #melodyの初期化
    melody = [0 for i in range(signature)]
    #note_orderの一番数字の大きいものを探す．同じ場合は最初のものを採用
    standard_note = note_order.index(max(note_order))
    melody[standard_note] = stem[measure]
    degree[standard_note] = adapt[(stem[measure] + 12 - key) % 12] #degreeを0から6で表す
    #前に行く
    if(standard_note > 0):
        for i in range(standard_note-1, -1, -1):
            if(note_tone[i+1] == 1): #前の音符が後の音符より低い場合
                rate = scale[(degree[i+1]+6) % 7]
            elif(note_tone[i+1] == -1): #前の音符が後の音符より高い場合
                rate = scale[(degree[i+1]) % 7]
            else :
                rate = 0
            melody[i] = melody[i+1] - rate*note_tone[i+1]
            degree[i] = adapt[(melody[i] + 12 - key) % 12]
    #後に行く
    if(standard_note < signature-1):
        for i in range(standard_note+1, signature):
            if(note_tone[i] == 1): #後の音符が前の音符より高い場合
                rate = scale[(degree[i-1]) % 7]
            elif(note_tone[i] == -1): #後の音符が前の音符より低い場合
                rate = scale[(degree[i-1]+6) % 7] 
            else :
                rate = 0
            melody[i] = melody[i-1] + rate*note_tone[i]
            degree[i] = adapt[(melody[i] + 12 - key) % 12]
    #note_orderが0の場合はmelodyを0にする
    for i in range(signature):
        if(note_order[i] == 0):
            melody[i] = 0
    return melody

#melodyをMIDIファイルに書き込むメソッド
def write_midi(note_order, melody):
    for i in range(signature):
        if(note_order[i] != 0):
            track.append(Message('note_on', note=melody[i], velocity=vel, time=0))
            track.append(Message('note_off', note=melody[i], velocity=vel, time=unit*note_order[i]))



init()
read_midi()
pattern = update_pattern()
for i in range(number_of_measure): 
    note_order = update_note_order(pattern[i]) 
    order_bank[i] = note_order
for i in range(number_of_measure):
    note_tone = update_note_tone(pattern[i])
    tone_bank[i] = note_tone
print(order_bank)
print(tone_bank)
for i in range(number_of_measure):
    melody = update_melody(order_bank[i], tone_bank[i], i, rate)
    melody_bank[i] = melody
for i in range(number_of_measure):
    write_midi(order_bank[i], melody_bank[i])
mid.save(filename)
