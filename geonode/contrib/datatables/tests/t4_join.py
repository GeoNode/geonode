from os.path import join
from msg_util import *
import pandas as pd

from tabular_test import TabularTest, INPUT_DIR

#pd.set_option('display.mpl_style', 'default') # Make the graphs a bit prettier
#figsize(15, 5)



def load_dataframe(fname):
    msgt('Loading dataframe: %s' % fname)
    tabular_fname = join(INPUT_DIR, fname)

    df = pd.read_csv(tabular_fname)  
    msg(df.dtypes)
    msg(list(df.columns.values))
    msg(df.describe())
    #msg(df['TRACTCE'])
    
    return df


if __name__ == '__main__':
    #df_income = load_dataframe('boston_income_73g.csv')    # TRACT
    df_income = load_dataframe('boston_income_73g-1-row.csv')    # TRACT
    df_census = load_dataframe('tl_2014_25_tract.csv')  # TRACTCE
    msgt('Pre-Merge')
    
    #msg(df_income.describe())
    #msg(df_census.describe())
    #df[(df.A == 1) & (df.D == 6)]
    
    """
    # Filter by tract
    df2 = df_income[(df_income['TRACT'] == 130300)]#df_income['TRACT'] == 130300
    msg(df2)
    # Save filtered dataframe to csv
    df2.to_csv(join(INPUT_DIR, 'boston_income_73g-1-row.csv'))
    """

    #msg([(df_income['TRACT'] == 130300)])    
    merged_pd = pd.merge(df_income, df_census, left_on='TRACT', right_on='TRACTCE', how='left')
    msgt('Post-Merge')
    msg(merged_pd.describe())
    msg(merged_pd)
    #print pd.merge(df_income, df_census, left_on='TRACT', right_on='TRACTCE', how='inner')
    
    #census_df = get_census_df()
    #print census_df
    #income_df = get_income_df()
    
#msg(ma_tigerlines_csv[:3])