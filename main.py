#!pip3 install crunch-cli --upgrade


# import and instantiante the crunch package in this notebook
import crunch
#crunch = crunch.load_notebook(__name__)


# authenticating the user and setting up the workspace
#!crunch --notebook setup resonant-poincare --token 8JOXos9WxbgwY3VpkC6vlYohkUvFUKMJwdokdZT9SbSdOW5VeeMMQiYFpI2FxXM3
# moving to the working directory
#%cd resonant-poincare


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
from tqdm import tqdm
import requests
#warnings.filterwarnings("ignore") # This is not advised in general, but it is used in this notebook to clean the presentation of results


# Getting the data
#X_train, y_train, X_test = crunch.load_data()


#X_train.head(10)


#X_train.tail(10)


#X_train.shape


#X_train.describe()


#X_train.nunique()


#max_date = np.max(X_train['date']) + 1
#max_feats = len(X_train.columns) 
#print(max_date,max_feats)


# number of assets per periods in the universe
#X_train.groupby(['date'])['id'].count().plot(figsize=(26,6))


#X_train['date'].value_counts().hist()


#y_train.nunique()


#y_train.head(10)


#np.sum(np.sum((X_train.isna()))) 


#fig, axs = plt.subplots(2, 2,figsize=(18,18))
#feats = ['1','3','10','400']
#ax = axs.flatten()

#for idx,a in enumerate(ax):
#    a.plot(X_train[feats[idx]])
#    a.plot(X_train[feats[idx]].rolling(20).mean())
#    a.plot(X_train[feats[idx]].rolling(200).mean())
#    a.plot(X_train[feats[idx]].rolling(2000).mean())
#    a.set_title('Feature ' +  feats[idx] + ' plot')
#    a.set(xlabel='Samples', ylabel='Feature values')
#    


#fig, axs = plt.subplots(2, 2,figsize=(18,18))
#ax = axs.flatten()
#for idx,a in enumerate(ax):
#    a.plot(X_train[feats[idx]].rolling(20000).mean())
#    a.set(xlabel='Samples', ylabel='Feature values')
#    a.set_title('Feature ' +  feats[idx] + ' plot')


#x_means_1, x_means_3,x_means_10,x_means_700 = [],[],[],[]
#x_means = [x_means_1, x_means_3,x_means_10,x_means_700]

#for i in range(max_date):
#    x_means_1.append(X_train.loc[X_train['date']==i,'1'].mean())
#    x_means_3.append(X_train.loc[X_train['date']==i,'3'].mean())
#    x_means_10.append(X_train.loc[X_train['date']==i,'10'].mean())
#    x_means_700.append(X_train.loc[X_train['date']==i,'400'].mean())

#fig, axs = plt.subplots(2, 2,figsize=(18,18))
#ax = axs.flatten()
#for idx,a in enumerate(ax):
#    a.plot(x_means[idx])
#    a.plot(pd.DataFrame(x_means[idx]).rolling(30).mean())
#    a.plot(pd.DataFrame(x_means[idx]).rolling(30).median())
#    a.set(xlabel='Samples', ylabel='Feature values')
#    a.set_title('Feature ' +  feats[idx] + 'mean per date plot')


import seaborn as sns


#gcorr = np.corrcoef(X_train.iloc[:,2:],rowvar=False) #numpy is much faster that pandas corr() method for large only-numerical data without missing values.


def plot_correlation_heatmap(corr):
    ax = sns.heatmap(
        corr, 
        vmin=-1, vmax=1, center=0,
        cmap=sns.diverging_palette(20, 220, n=200),
        square=True
    )
    ax.set_xticklabels(
        ax.get_xticklabels(),
        rotation=45,
        horizontalalignment='right'
    )


#plot_correlation_heatmap(gcorr)


#corr = np.corrcoef(X_train.iloc[:,2:20],rowvar=False)
#plot_correlation_heatmap(corr)


#corr = np.corrcoef(X_train.iloc[:,20:60],rowvar=False)
#plot_correlation_heatmap(corr)


#corr = np.corrcoef(X_train.iloc[:,100:180],rowvar=False)
#plot_correlation_heatmap(corr)


#corr = np.corrcoef(X_train.iloc[:,2:],rowvar=False)
#np.min(corr)


#cs= np.sort(corr.flatten())
#cs[-466:-452]


#pd.DataFrame(gcorr.flatten()).hist()


#X_train.iloc[:,2:22].hist(bins=50,figsize=(18, 18))
#plt.show()


#X_train.iloc[:,2:22].plot(kind='density', subplots=True, layout=(5,4), sharex=False)
#plt.show()


#X_train.iloc[:,22:42].hist(bins=50,figsize=(18, 18))
#plt.show()


#X_train.iloc[:,90:136].hist(bins=50,figsize=(18, 18))
#plt.show()


#y_train.y.hist(bins=50,figsize=(8, 4))
#plt.show()


#!pip install statsmodels


from statsmodels.graphics.gofplots import qqplot


#fig, axs = plt.subplots(2, 2,figsize=(18,18))
#ax = axs.flatten()
#feats = [8,16,32,64] #We explore a different set of features
#for idx,a in enumerate(ax):
#    qqplot(X_train.iloc[:,feats[idx]], line='s',ax=a)
#plt.show()


from scipy.stats import shapiro


#p_vals_shapiro = []
#for i in range(2,max_feats):
#    stat, p = shapiro(X_train.iloc[:,i])
#    p_vals_shapiro.append(p)
#sum(np.array(p_vals_shapiro)>=0.05)
#sum(np.array(p_vals_shapiro)>=1)


#sum(np.array(p_vals_shapiro)>=0.05)


from scipy.stats import normaltest
#p_vals_DAgostinok2 = [] 
#for i in range(2,max_feats):
#    stat, p = normaltest(X_train.iloc[:,i])
#    p_vals_DAgostinok2.append(p)
#sum(np.array(p_vals_DAgostinok2)>=0.05)


from scipy.stats import anderson
#p_vals_anderson = [] 
#for i in range(2,max_feats):
#    result = anderson(X_train.iloc[:,i],dist='norm')
#    fail = False
#    for i in range(len(result.critical_values)):
#        sl, cv = result.significance_level[i], result.critical_values[i]
#        if result.statistic >= result.critical_values[i]:
#            p_vals_anderson.append(0)
#            fail = True
#            break
#    if not fail:
#        p_vals_anderson.append(1)
#sum(np.array(p_vals_anderson)>=0.05)


from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.graphics.tsaplots import plot_pacf


#df_global = X_train.groupby('date').mean()
#df_global = X_train.groupby('date').std()


#fig, axs = plt.subplots(4,2,figsize=(18,20))
#ax = axs.flatten()
#feats = ['5','25','125','425']
#for i in range(4):
#    a1 = ax[2*i]
#    a2 =  ax[2*i+1]
#    plot_acf(df_global[feats[i]],ax=a1)
#    plot_pacf(df_global[feats[i]], lags=30,ax=a2) 
#    a1.set_title('Feature ' +  feats[i] + ' Autocorrelation plot')
#    a2.set_title('Feature ' +  feats[i] + ' Partial autocorrelation plot')
#plt.show()


#fig, axs = plt.subplots(1,2,figsize=(18,5))
#ax = axs.flatten()
#plot_acf(X_train.iloc[0:1000,3],ax=ax[0])
#plot_pacf(X_train.iloc[0:1000,3],lags=30,ax=ax[1])
#plt.show()


#X_train = X_train.drop('id',axis=1)
#y_train = y_train.drop('id',axis=1)
#max_feats-=1


def calc_dist(l_norm,p1,p2): #A simple but general l_p distance method between 2 points of arbitraty dimension
    if l_norm == 0: #In here we use 0 to represent inf
        return np.max(np.abs(np.array(p1) - np.array(p2)))
    else:
        return np.float_power(sum(np.abs(np.power(np.array(p1) - np.array(p2),l_norm))),1/l_norm)

def compute_features_of_interest_local(data): #This is per date, will be called once per existing date
    n,d = data.shape        
    feats = list(data.columns)[1:]    
    centroid = []
    sds = []
    data.loc[:,'sum_rank'] = 0
    data.loc[:,'sum_vals'] = 0
    for feat in feats:
        df = data[feat]
        dfs = np.array(sorted(enumerate(df),key= lambda x: x[1],reverse=True))[:,0] #rankings of each feature w.r.t the others (low rank higher score) 
        data.loc[:,'sum_rank'] = dfs + data.loc[:,'sum_rank']     
        centroid.append(df.mean())
    data.loc[:,'centroid_l2'] = data.loc[:,feats].apply(lambda x: calc_dist(2,centroid,x),axis=1)
    data.loc[:,'centroid_l1'] = data.loc[:,feats].apply(lambda x: calc_dist(1,centroid,x),axis=1)
    data.loc[:,'centroid_linf'] = data.loc[:,feats].apply(lambda x: calc_dist(0,centroid,x),axis=1)
    data.loc[:,'sum_vals'] = data.apply(lambda x: sum(x[1:max_feats]),axis=1) #We quickly can add another feature to summarize the overall ranking
    return data


#X_train_ex = [] #Saves the result of the expanded data at every date
#for date in tqdm(range(max_date)):
#    X_train_ex.append(compute_features_of_interest_local(X_train.loc[X_train['date']==date,:]))


#X_train_2 = pd.concat(X_train_ex) 


import snappy
import fastparquet

#X_train_2.to_parquet('X_train_2.snap.parquet',compression='snappy')# After a lenghtly feature computation, We will save our data at this point


#X_train_2.memory_usage().sum()/1024**2 #It occupies roughly 1.5Gb in this form


#X_train_2 = pd.read_parquet('X_train_2.snap.parquet')
#y_train = pd.read_parquet('y_train.parquet',engine='pyarrow')


#X_train_2


from sklearn.model_selection import TimeSeriesSplit


def TemporalCV(List_models,X_data,y_data,n_splits=5,max_train_size=None,test_size=None):
    X = np.array(list(range(max_date))) #Now this is dates, which is where we make the splits, instead of using rows directly
    tscv = TimeSeriesSplit(n_splits=n_splits, max_train_size= max_train_size,test_size=test_size) 
    stats_CV = {} #Storage of performance 
    count = 0
    for train, test in tscv.split(X):
        fold_train_X = X_data.loc[np.logical_and(X_data['date'] >= train[0],X_data['date'] <= train[-3]),:]
        fold_train_y = y_data.loc[np.logical_and(y_data['date'] >= train[0], y_data['date'] <= train[-3]),:]

        fold_test_X = X_data.loc[np.logical_and(X_data['date'] >= test[0], X_data['date'] <= test[-1]),:]
        fold_test_y = y_data.loc[np.logical_and(y_data['date'] >= test[0], y_data['date'] <= test[-1]),:]
        count+=1
        sample_pred = fold_test_y.copy()
        for model in List_models:
            model_name = model.__class__.__name__            
            model.fit(fold_train_X,fold_train_y.loc[:,['y']])  
            preds = model.predict(fold_test_X)
            sample_pred.loc[:,'y'] = preds.astype(float) 
            score = get_rank_corr_score(sample_pred,fold_test_y)            
            if model_name in stats_CV:
                stats_CV[model_name].append(score)
            else:
                stats_CV[model_name] = [score]
    return stats_CV

def get_rank_corr_score(y_preds,y_trues):
    rank_pred = y_preds.groupby('date',group_keys=True).apply(lambda x: x.rank(pct=True, method="first"))    
    correlation_score = np.corrcoef(rank_pred['y'],y_trues['y'])[0,1]
    return correlation_score


import sklearn.linear_model


#List_models = [
#    sklearn.linear_model.LinearRegression(),
#    sklearn.linear_model.Lasso(alpha=0.001),
#    sklearn.linear_model.ElasticNet(alpha=0.6,l1_ratio=0.001),    
#    sklearn.linear_model.Ridge(alpha=0.6) 
#] 


#statsCV = TemporalCV(List_models=List_models,X_data=X_train_2, y_data = y_train,n_splits=10)
#for key, item in statsCV.items():
#    plt.plot(item)
#    print('Our ' + key + ' model obtained an average score of ' + str(np.mean(item)) + ' in our CV scheme, with a standard deviation of ' + str(np.std(item)))
#plt.legend(statsCV.keys())


#statsCV0 = TemporalCV(List_models=List_models,X_data=X_train_2.iloc[:,0:max_feats], y_data = y_train,n_splits=10)
#for key, item in statsCV0.items():
#    plt.plot(item)
#    print('Our ' + key + ' model obtained an average score of ' + str(np.mean(item)) + ' in our CV scheme, with a standard deviation of ' + str(np.std(item)))
#plt.legend(statsCV0.keys())   


#statsCV1 = TemporalCV(List_models=List_models,X_data=X_train_2.drop(X_train_2.columns[1:max_feats],axis=1), y_data = y_train,n_splits=10)
#for key, item in statsCV1.items():
#    plt.plot(item)
#    print('Our ' + key + ' model obtained an average score of ' + str(np.mean(item)) + ' in our CV scheme, with a standard deviation of ' + str(np.std(item)))
#plt.legend(statsCV1.keys()) 


#statsCV2 = TemporalCV(List_models=List_models,X_data=X_train_2, y_data = y_train,n_splits=10,max_train_size=10,test_size=10)
#for key, item in statsCV2.items():
#    plt.plot(item)
#    print('Our ' + key + ' model obtained an average score of ' + str(np.mean(item)) + ' in our CV scheme, with a standard deviation of ' + str(np.std(item)))
#plt.legend(statsCV2.keys())


#statsCV3 = TemporalCV(List_models=List_models,n_splits=10,X_data=X_train_2, y_data = y_train,max_train_size=20,test_size=20)
#for key, item in statsCV3.items():
#    plt.plot(item)
#    print('Our ' + key + ' model obtained an average score of ' + str(np.mean(item)) + ' in our CV scheme, with a standard deviation of ' + str(np.std(item)))
#plt.legend(statsCV3.keys()) 


#statsCV4 = TemporalCV(List_models=List_models,X_data=X_train_2, y_data = y_train,n_splits=10,max_train_size=20)
#for key, item in statsCV4.items():
#    plt.plot(item)
#    print('Our ' + key + ' model obtained an average score of ' + str(np.mean(item)) + ' in our CV scheme, with a standard deviation of ' + str(np.std(item)))
#plt.legend(statsCV4.keys()) 


#statsCV5 = TemporalCV(List_models=List_models,X_data=X_train_2, y_data = y_train,n_splits=10,max_train_size=60,test_size=20)
#for key, item in statsCV5.items():
#    plt.plot(item)
#    print('Our ' + key + ' model obtained an average score of ' + str(np.mean(item)) + ' in our CV scheme, with a standard deviation of ' + str(np.std(item)))
#plt.legend(statsCV5.keys()) 
