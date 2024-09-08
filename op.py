import pandas as pd
import numpy as np



def prepare_data(df, years, ratings, weight):

    df = df[df['titleType']=='movie']
    
    df['startYear'] = pd.to_numeric(df['startYear'], errors='coerce').astype('Int64')
    df = df[df['startYear'].isin(years)]
    df = pd.merge(df, ratings, on = 'tconst')
    df=df.drop(columns=['titleType'])
    df['genres']=df['genres'].apply(lambda x : x.split(","))
    df['impact']=weight(df['averageRating'])*df['numVotes']
    df=df.sort_values(by=['impact'], ascending=False, ignore_index=True )
    df["order"]=[x+1 for x in range(df["tconst"].size)]
    
    return df

def compute_years(start,end):
    if isinstance(start, int) and isinstance(end, int):
        if start > end:
            raise ValueError("Time interval is empty")
        else:
            return range(start,end+1)
    else:
        raise ValueError("Start year and end year should be integers")

def prepare_countries(df, title_akas, country_codes):
    
    title_akas.rename(columns = {'titleId':'tconst'}, inplace = True)
    original_titles = title_akas[title_akas["isOriginalTitle"]==1]
    df_countries = pd.merge(title_akas,original_titles, on = ["tconst", "title"], how='inner')
    df_countries = df_countries[df_countries["isOriginalTitle_x"]==0]
    df_countries = df_countries.drop(["isOriginalTitle_x","region_y", "isOriginalTitle_y"], axis=1)
    df_countries.rename(columns = {'region_x':'region'}, inplace = True)
    df_countries = pd.merge(df, df_countries, on='tconst')
    df_countries["duplicated"]= df_countries.duplicated(subset=['tconst'], keep=False)
    df_countries = pd.merge(df_countries, country_codes, on ='region')

    return df_countries

def unique_count(df_countries, ids):
     return df_countries[df_countries["duplicated"]==False]["tconst"].size/ids.size

def top(df_countries, number_of_best_movies):

    top=df_countries[df_countries["order"]<=number_of_best_movies]
    top_countries = top["Country Name"].unique()
    list =[]
    for country in top_countries:
        list.append(len(top[top["Country Name"]==country]))
    toplist = pd.DataFrame()
    toplist["country"]=top_countries
    toplist["number of movies in top " + str(number_of_best_movies)] = list
    toplist = toplist.sort_values(by=["number of movies in top " + str(number_of_best_movies)], ascending = False)
    return toplist[0:10]



def prepare_mean(df, name, years):
    years1=[str(year) for year in years]
    df1 =df[df.columns.intersection(years1)]
    df["mean_"+name]=df1.mean(axis=1, skipna=True, numeric_only=True)
    df = df[['Country Name', "mean_"+name]]
    return df

def prepare_country_data(years, gdp, gdp_per_capita, population,strong_impact_by_countries, weak_impact_by_countries):

    country_data = prepare_mean(gdp,"gdp",years)
    country_data = pd.merge(country_data, prepare_mean(gdp_per_capita,"gdp_per_capita",years), on='Country Name')
    country_data = pd.merge(country_data, prepare_mean(population,"population",years), on='Country Name')
    country_data = pd.merge(country_data, strong_impact_by_countries, on='Country Name')
    country_data = pd.merge(country_data, weak_impact_by_countries, on='Country Name')

    country_data["votes/gdp"]=country_data["numVotes"]/country_data["mean_gdp"]
    country_data["impact/gdp"]=country_data["impact"]/country_data["mean_gdp"]
    country_data["votes/gdp_per_capita"]=country_data["numVotes"]/country_data["mean_gdp_per_capita"]
    country_data["impact/gdp_per_capita"]=country_data["numVotes"]/country_data["mean_gdp_per_capita"]
    country_data["votes/population"]=country_data["numVotes"]/country_data["mean_population"]
    country_data["impact/population"]=country_data["impact"]/country_data["mean_population"]

    for col_name in ["mean_gdp", "mean_gdp_per_capita", "mean_population", "votes/gdp", "impact/gdp",  "votes/gdp_per_capita", "impact/gdp_per_capita", "votes/population", "impact/population" ]:
        country_data = country_data.sort_values(by=[col_name], ascending=False)
        country_data[ "rank " + col_name ]=[x+1 for x in range(len(country_data)) ]

    return country_data

def prepare_hegemony(country_data):
    hegemony = pd.DataFrame()
    
    hegemony["country"] = country_data["Country Name"]
    hegemony["weak hegemony by GDP"] = country_data["rank mean_gdp"] - country_data["rank votes/gdp"]
    hegemony["weak hegemony by GDP/population"] = country_data["rank mean_gdp_per_capita"] - country_data["rank votes/gdp_per_capita"]
    hegemony["weak hegemony by population"] = country_data["rank mean_population"] - country_data["rank votes/population"]
    hegemony["strong hegemony by GDP"] = country_data["rank mean_gdp"] - country_data["rank impact/gdp"]
    hegemony["strong hegemony by GDP/population"] = country_data["rank mean_gdp_per_capita"] - country_data["rank impact/gdp_per_capita"]
    hegemony["strong hegemony by population"] = country_data["rank mean_population"] - country_data["rank impact/population"]

    return hegemony

def prepare_pl(df, df_countries):
    pl = df_countries[df_countries["region"]=="PL"]
    pl = pl[pl["duplicated"]==False]
    pl = pd.merge(pl[["tconst","title"]], df, on ='tconst')
    pl_genres = pl.explode("genres")
    pl_com = pl_genres[pl_genres["genres"]=="Comedy"]
    return pl_com

def prepare_cz(df, df_countries):
    cz = df_countries[df_countries["region"].isin(["CZ","CSHH","SK"])]
    cz = cz[cz["duplicated"]==False]
    cz = pd.merge(cz[["tconst", "title"]], df, on ='tconst')
    cz_genres = cz.explode("genres")
    cz_com = cz_genres[cz_genres["genres"]=="Comedy"]
    return cz_com