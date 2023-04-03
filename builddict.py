from bs4 import BeautifulSoup 
import requests
import xlrd
import pandas as pd
from pathlib import Path
import time
import datetime as dt
import time
from pykakasi import kakasi as Kakasi
import unicodedata

#Open new and old dictionaries
sheet = Path(__file__).parent / "vdrj.xls"
wbc = xlrd.open_workbook(sheet, encoding_override='utf-8')

#Move contents of old dictionary to lists
df = pd.read_excel(sheet, sheet_name="list", usecols="C", dtype = object)
df2 = pd.read_excel(sheet, sheet_name="list", usecols="A", dtype = object)
data = {'Japanese': [], 'Kana': []}
newdict_df = pd.DataFrame(data)
wordlist = df.values.tolist()
kanlist = df2.values.tolist()


def is_japanese_char(ch):
    c = ord(ch)
    return (
        0x4E00 <= c <= 0x9FFF  # CJK Unified Ideographs (Kanji)
        or 0x3040 <= c <= 0x309F  # Hiragana
        or 0x30A0 <= c <= 0x30FF  # Katakana
    )
def normalize_and_filter_japanese(text):
    normalized_text = unicodedata.normalize("NFKC", text)
    return ''.join(filter(is_japanese_char, normalized_text))

def grabword(w):    #Grab related words/phrases to given word (w) from Weblio's dictionary
    #Get HTML content of dictionary
    max_retries = 10
    retry_wait_time = 10  # seconds
    
    for attempt in range(max_retries):
        try:
            url = f'https://ejje.weblio.jp/content/{w}'
            response = requests.get(url)
            break
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                print(f"Request failed with error: {e}. Retrying in {retry_wait_time} seconds...")
                time.sleep(retry_wait_time)
            else:
                print(f"Request failed after {max_retries} attempts. Skipping word...")
                return []
    soup = BeautifulSoup(response.content, 'html.parser')

    #Grab all related word element from dictionary page
    relatedwords = soup.find_all('div', class_='werbjJ') 
    morewords = []

    #Isolate words and send to related word list
    for word in relatedwords: 
        awesome = word.find_all('p')[-1].text.strip() 
        morewords.append(awesome)

    return morewords

def kanaconvert(word):
    kakasi_instance = Kakasi()
    kakasi_instance.setMode("J", "K")  # Convert from Japanese (kanji and hiragana) to katakana
    kakasi_instance.setMode("H", "K")  # Convert from hiragana to katakana
    kakasi_instance.setMode("K", "K")  # Convert from katakana to katakana
    converter = kakasi_instance.getConverter()
    kana = converter.do(word)
    return kana


def systemstart(word): #Gets isolated word list and un-nests it
    #Grab related words
    thelist = grabword(word)

    #Check if there are any words in the related words list
    try:
        cool = thelist[0]
    except IndexError:
        pass
    
    #Add original word to related words list
    thelist.append(word[0])
    return thelist

def frmtdelta(delta): #Elapsed time function (from stackoverflow)
    d = {"days": delta.days}
    d["hr"], rem = divmod(delta.seconds, 3600)
    d["min"], d["sec"] = divmod(rem, 60)
    return "{days}d, {hr}h, {min}m, {sec}s".format(**d)


def checktime(): #Update time elapsed (also technically from stackoverflow)
    now = time.time()
    delta = dt.timedelta(seconds=int(now - start))
    elapsed = frmtdelta(delta)
    time.sleep(.1)
    return elapsed

#Set up variables and open newdict.xlsx
start = time.time() 
numb = 0
other = 0
checklist = []
duplicates = 0

#Grab related words for every word in original dictionary
for word in kanlist:
    other += 1
    success = systemstart(word)
    for y in success:
        normaly = normalize_and_filter_japanese(y)
        z = kanaconvert(normaly)
        numb += 1
        newdict_df = pd.concat([newdict_df, pd.DataFrame({'Japanese': [normaly], 'Kana': [z]})], ignore_index=True)
    # Remove the following line:
    # checklist.extend([normalize_and_filter_japanese(y) for y in set(success)])
    progress = int(100*(other/50816))
    magnitude = round(numb/other, 1)
    elapsedtime = checktime()
    print(f'{progress}% done... ({other} out of 50816 processed)')
    print(f'New dictionary length: {numb} ({magnitude}x bigger so far!)')

    
#Give me the stats after the job is done
#workbook.close()
length1 = len(newdict_df)
newdict_df = newdict_df.drop_duplicates(subset=["Japanese", "Kana"])
length2 = len(newdict_df)
# Save the DataFrame back to the newdict.xlsx file
duplicates = length1 - length2
numb -= duplicates
magnitude = round(numb/other, 1)
newdict_df.to_excel("newdict.xlsx", index=False)
print("Done!")
print(f"Words processed: {other} out of 50816")
print(f"Words added: {numb} (a {magnitude}x increase!)")
print(f"Duplicates found: {duplicates}")
print(f"Success rate: {progress}%")
print(f"Time spent: {elapsedtime}")
print(f"All in all, a pretty nice Monday! :)")

