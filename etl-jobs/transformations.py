import sys
import boto3
import pandas as pd
import numpy as np
from awsglue.utils import getResolvedOptions

def format_review_comments(df):
    for i in range(12, 6, -1):
        df_filted = df[~df[f'Unnamed: {i}'].isna()]
        complete_comment = df_filted['review_comment_message']
        for j in range(5, i):
            complete_comment = ',' + df_filted[df_filted.columns[j]]
        df_filted['review_comment_message'] = complete_comment
        df_filted['review_creation_date'] = df_filted[df_filted.columns[i-1]]
        df_filted['review_answer_timestamp'] = df_filted[df_filted.columns[i]]
        for j in range(7, 13):
            df_filted[f'Unnamed: {j}'] = np.nan
        df.update(df_filted)
    df = df.loc[:, df.columns[:7]]
    return df

args = getResolvedOptions(sys.argv, ['input_bucket', 'output_bucket'])

s3 = boto3.client('s3', region_name='us-east-1')

resp = s3.list_objects_v2(Bucket=args['input_bucket'], Prefix='olist')
if 'Contents' not in resp:
    print(f'Bucket {args["input_bucket"]} is empty')
    exit()
contents = resp['Contents']

for content in contents:
    df = pd.read_csv(f's3://{args["input_bucket"]}/{content["Key"]}')

    # Rules for reviews dataset
    #  - Format comments with multiple lines and comma
    #  - Exclude unnamed fields 
    if 'order_reviews' in content['Key']:
        df = format_review_comments(df)

    # Rules for sellers
    #  - Exclude unnecessary columns
    if 'sellers' in content['Key']:
        df = df.drop(['seller_city', 'seller_state'], axis=1)

    new_key = f'{content["Key"].rsplit(".", 1)[0]}.parquet'
    df.to_parquet(f's3://{args["output_bucket"]}/{new_key}')