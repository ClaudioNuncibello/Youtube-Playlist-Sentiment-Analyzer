import urllib.request
import os

def download_file(url, filename):
    urllib.request.urlretrieve(url, filename)

def main():
    urls = [
        "https://s3.amazonaws.com/auxdata.johnsnowlabs.com/public/resources/en/lemma-corpus-small/lemmas_small.txt",
        "https://s3.amazonaws.com/auxdata.johnsnowlabs.com/public/resources/en/sentiment-corpus/default-sentiment-dict.txt"
    ]

    for url in urls:
        filename = os.path.basename(url)
        download_file(url, filename)
        print(f"File {filename} scaricato.")

if __name__ == "__main__":
    main()
