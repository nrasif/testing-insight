import pandas as pd

def uatProgress_proc(path):
    df_uat = pd.read_excel(path)
    df_uat.ffill(inplace=True)
    df_uat[['Target Execution', 'Execution', 'Passed', 'Failed']] = df_uat[['Target Execution', 'Execution', 'Passed', 'Failed']].applymap(lambda x: x*100).astype(float)
    df_uat["Tanggal"] = pd.to_datetime(df_uat["Tanggal"], format="%m/%d/%Y", errors='coerce')
    return df_uat