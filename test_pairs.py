import pandas as pd
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

CSV_PATH = r"C:\Users\priya\.cache\kagglehub\datasets\thoughtvector\customer-support-on-twitter\versions\10\twcs\twcs.csv"

def analyze_brand(brand_name="AppleSupport", nrows=500000):
    print(f"Reading {nrows} rows from {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH, nrows=nrows)
    
    # Filter brand replies
    brand_replies = df[(df['author_id'] == brand_name) & (df['inbound'] == False)].copy()
    print(f"Total {brand_name} replies in sample: {len(brand_replies)}")
    
    # Filter inbound tweets
    inbound_tweets = df[df['inbound'] == True].copy()
    
    # Merge on in_response_to_tweet_id
    pairs = pd.merge(
        brand_replies,
        inbound_tweets,
        left_on='in_response_to_tweet_id',
        right_on='tweet_id',
        suffixes=('_reply', '_customer')
    )
    
    print(f"Successfully reconstructed {len(pairs)} single-turn pairs!")
    
    print("\n--- SAMPLE PAIRS ---")
    for idx, row in pairs.head(10).iterrows():
        print(f"Pair #{idx+1}:")
        print(f"Customer Tweet ({row['tweet_id_customer']}): {row['text_customer']}")
        print(f"Brand Reply    ({row['tweet_id_reply']}): {row['text_reply']}")
        print("-" * 60)
        
    return pairs

if __name__ == "__main__":
    analyze_brand("AppleSupport", nrows=500000)
