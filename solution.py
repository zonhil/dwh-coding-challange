import pandas as pd 
import numpy as np 
import os.path
import json 
import glob
import webbrowser


def df_merge(folder):
    path_list=glob.glob(os.path.join(folder,'*.json'))
    df=pd.DataFrame()
    for file_path in path_list:
        data_load=json.load(open(file_path))
        data_normal=pd.json_normalize(data_load)    
        df=df.append(data_normal)    
    df=df.sort_values('ts')
    return df   

def df_set(df,column):
    set_col='set.'+column
    data_col='data.'+column    
    if data_col not in df:
      df[data_col] = np.nan  
    df[data_col] = np.where(df[set_col].notnull(), df[set_col], df[data_col])
    return df    

def df_update(df):
    for col in df.columns:
        if col[:3]=='set':
            column=col[4:] 
            df_set(df,column)
    return df

def df_fill(df):
    for col in df.columns:
        if col[:4]=='data':
            df[col].fillna(method='ffill',inplace=True) 
    return df

def df_table(folder):
    df=df_merge(folder)
    df=df_update(df)   
    df=df_fill(df)
    df['date_time'] = df['ts'].values.astype(dtype='datetime64[ms]')       
    return df

def print_html(df,name,comments=''):
    foldername='solution//'+name
    url=foldername+'.html'
    # url=name+'.html'
    html_file=df.to_html(url)
    html_file = open(url)
    content = html_file.read()
    html_file.close()
    begin = """
        <html>
        <head>
        <style>
        thead {color: green;}
        tbody {color: black;}
        tfoot {color: red;}
        table, th, td {
            border: 1px solid black;
            text-align: left;
        }       
        </style>
        </head>
        <body>
        <h4>
        """ + name.upper() + "</h4>"

    if comments!='':
        note="<br>"+comments.replace("-","<br> -")
    else:
        note=''

    end = """
        </body>
        </html>
        """
    html_file = open(url, "w")
    html_file.write(begin)
    html_file.write(content)
    html_file.write(note)
    html_file.write(end)
    # url='solution/'+name+'.html'
    filename = 'file:///'+os.getcwd()+'/solution/'+name+'.html'
    webbrowser.open(filename, new=2) 

# start 
# project_dir=os.path.abspath(__file__ + '/../../')
project_dir=os.path.abspath(__file__ + '/../')
accounts_dir=project_dir+'/data/accounts/'
cards_dir=project_dir+'/data/cards/'
savings_dir=project_dir+'/data/savings_accounts/'

df_accounts=df_table(accounts_dir)
df_cards=df_table(cards_dir)
df_savings=df_table(savings_dir)


df_cards['data.credit_used'] = df_cards['data.credit_used'].replace(0, np.nan)
df_cards['prev_credit_used']=df_cards['data.credit_used'].shift(1).fillna(0)
df_cards['transaction']=df_cards['data.credit_used']-df_cards['prev_credit_used']
df_cards=df_cards.drop('prev_credit_used',1)

df_savings['prev_balance']=df_savings['data.balance'].shift(1).fillna(0)
df_savings['transaction']=df_savings['data.balance']-df_savings['prev_balance']
df_savings=df_savings.drop('prev_balance',1)

df_accounts_savings=df_accounts.loc[df_accounts['set.savings_account_id'].notnull()]
df_accounts_savings=df_accounts_savings.drop(['set.card_id','data.card_id'],1)
df_accounts_savings=pd.merge(df_accounts_savings,df_savings,on='data.savings_account_id')

df_accounts_cards=df_accounts.loc[df_accounts['set.card_id'].notnull()]
df_accounts_cards=df_accounts_cards.drop(['set.savings_account_id','data.savings_account_id'],1)
df_accounts_cards=pd.merge(df_accounts_cards,df_cards,on='data.card_id')

df_history=df_accounts_cards.append(df_accounts_savings,ignore_index=True)
df_history=df_history.sort_values('ts_y')
df_history['transaction'] = df_history['transaction'].replace(np.nan,0)
df_history['account_number'] = df_history['data.account_id']+'-'+np.where( \
    df_history['data.savings_account_id'].notnull(), \
    df_history['data.savings_account_id'], \
    df_history['data.card_id'])
df_history['account_type'] = np.where(df_history['data.savings_account_id'].notnull(), 'savings', 'credit card')
df_history['date_time']=df_history.pop('date_time_y')
df_history['transaction']=df_history.pop('transaction') 
df_history=df_history.reset_index(drop=True)

df_transaction=df_history[['date_time','account_number','account_type','transaction']].copy().replace(0,np.nan).dropna()
df_transaction=df_transaction.reset_index(drop=True)

with pd.ExcelWriter('solution/solution.xlsx') as writer:  
    df_accounts.to_excel(writer, sheet_name='accounts')
    df_cards.to_excel(writer, sheet_name='cards')
    df_savings.to_excel(writer, sheet_name='savings')
    df_history.to_excel(writer, sheet_name='history')
    df_transaction.to_excel(writer, sheet_name='transaction')

# Task 1: Print each tables
print('Accounts Table:')
print(df_accounts)
print_html(df_accounts, 'accounts')
print('Cards Table:')
print(df_cards)
print_html(df_cards, 'cards')
print('Savings Table:')
print(df_savings)
print_html(df_savings, 'savings')

# Task 2: Print joined table
print('History Table:')
print(df_history)
print_html(df_history, 'history')

# Task 3: Print transactions
print('Transaction Table:')
print(df_transaction)
count_total=df_transaction.shape[0]
count_savings=df_transaction[df_transaction['account_type']=='savings'].count()['account_type']
count_cards=df_transaction[df_transaction['account_type']=='credit card'].count()['account_type']
count_savings_credit=df_transaction[(df_transaction['account_type']=='savings') & (df_transaction['transaction']>=0)].count()['account_type']
count_savings_debit=df_transaction[(df_transaction['account_type']=='savings') & (df_transaction['transaction']<0)].count()['account_type']
comments= \
    f'''
    Summary: 
    - Total: {count_total} transaction(s)
    - Credit cards: {count_cards} transaction(s)
    - Savings: {count_savings} transaction(s) ({count_savings_credit} credit & {count_savings_debit} debit) 
    '''
print(comments)
print_html(df_transaction, 'transaction',comments)

