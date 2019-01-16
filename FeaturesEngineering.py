from pathlib import Path

import numpy as np
import pandas as pd

from FeaturesFunctions import *
from constants import *

# %% ~~~~~ GLOBAL SETTINGS ~~~~~
# Pandas initialization
pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 80)
pd.set_option('display.float_format', lambda x: '{:.3f}'.format(x))


# %% ~~~~~ CONSTANTS ~~~~~
NONE_VALUE = 'None'
columns_to_drop = []


# %% ~~~~~ COMMON MAPPINGS ~~~~~
qualities_dict = {NONE_VALUE: 0, 'Po': 1, 'Fa': 2, 'TA': 3, 'Gd': 4, 'Ex': 5}
fin_qualities_dict = {NONE_VALUE: 0, "Unf": 1, "LwQ": 2, "Rec": 3, "BLQ": 4, "ALQ": 5, "GLQ": 6}


# %% ~~~~~ Train & test loading ~~~~~
train_df = pd.read_csv(Path(dataset_dir, 'train.csv'))
test_df = pd.read_csv(Path(dataset_dir, 'test.csv'))


# %% ~~~~~ Removing outliers ~~~~~
# As suggested by many participants, we remove several outliers
# %% Dropping outliers
out = [30, 88, 462, 631, 1322]
train_df = train_df.drop(train_df.index[out])
train_df.drop(train_df[(train_df['OverallQual'] < 5) & (train_df['SalePrice'] > 200000)].index, inplace=True)
train_df.drop(train_df[(train_df['GrLivArea'] > 4000) & (train_df['SalePrice'] < 300000)].index, inplace=True)
train_df.reset_index(drop=True, inplace=True)


# %% ~~~~~ Log Sale Price ~~~~~
y_train = np.log1p(train_df['SalePrice'])
train_df = train_df.drop(columns=['SalePrice'])


# %% ~~~~~ Drop Id column ~~~~~
train_ids = train_df['Id']
test_ids = test_df['Id']
train_df = train_df.drop(columns=['Id'])
test_df = test_df.drop(columns=['Id'])


# %% ~~~~~ Concatenate train & test ~~~~~
train_len = train_df.shape[0]
test_len = test_df.shape[0]
complete_df = pd.concat([train_df, test_df]).reset_index(drop=True)
assert complete_df.shape[0] == train_len + test_len


# %% MSZoning: Identifies the general zoning classification of the sale.
#
#        A    Agriculture
#        C    Commercial
#        FV   Floating Village Residential
#        I    Industrial
#        RH   Residential High Density
#        RL   Residential Low Density
#        RP   Residential Low Density Park
#        RM   Residential Medium Density
#
# -> Categorical feature, maybe we should split this feature into two (Residential/Other) because of the order.
complete_df['MSZoning'] = complete_df.groupby('MSSubClass')['MSZoning'].transform(lambda x: x.fillna(x.mode()[0]))
complete_df = ohe(complete_df, 'MSZoning')


# %% MSSubClass: Identifies the type of dwelling involved in the sale.
#
#         20  1-STORY 1946 & NEWER ALL STYLES
#         30  1-STORY 1945 & OLDER
#         40  1-STORY W/FINISHED ATTIC ALL AGES
#         45  1-1/2 STORY - UNFINISHED ALL AGES
#         50  1-1/2 STORY FINISHED ALL AGES
#         60  2-STORY 1946 & NEWER
#         70  2-STORY 1945 & OLDER
#         75  2-1/2 STORY ALL AGES
#         80  SPLIT OR MULTI-LEVEL
#         85  SPLIT FOYER
#         90  DUPLEX - ALL STYLES AND AGES
#        120  1-STORY PUD (Planned Unit Development) - 1946 & NEWER
#        150  1-1/2 STORY PUD - ALL AGES
#        160  2-STORY PUD - 1946 & NEWER
#        180  PUD - MULTILEVEL - INCL SPLIT LEV/FOYER
#        190  2 FAMILY CONVERSION - ALL STYLES AND AGES
#
# -> Categorical feature, maybe with some order.
complete_df = ohe(complete_df, 'MSSubClass')


# %% LotFrontage: Linear feet of street connected to property
#
# -> Group by neighborhood and fill in missing value by the median LotFrontage of all the neighborhood
complete_df['LotFrontage'] = complete_df.groupby('Neighborhood')['LotFrontage'].transform(lambda x: x.fillna(x.median()))


# %% LotArea: Lot size in square feet
#
# -> TODO: rescaling? luca: ?


# %% Street: Type of road access to property
#
#        Grvl Gravel
#        Pave Paved
#
# complete_df['IsStreetPaved'] = (complete_df['Street'] == 'Pave') * 1
# complete_df = ohe(complete_df, 'Street')
# -> Counter({'Pave': 2904, 'Grvl': 12}) TODO drop?
columns_to_drop.append('Street')


# %% Alley: Type of alley access to property
#
#        Grvl Gravel
#        Pave Paved
#        NA   No alley access
#
complete_df['Alley'].fillna(NONE_VALUE, inplace=True)
complete_df = ohe(complete_df, 'Alley')


# %% LotShape: General shape of property
#
#        Reg  Regular
#        IR1  Slightly irregular
#        IR2  Moderately Irregular
#        IR3  Irregular
#
# -> Counter({'Reg': 1859, 'IR1': 966, 'IR2': 76, 'IR3': 15})
# -> So we can just transform this feature into a boolean one: IsLotShapeRegular
complete_df['IsRegularLotShape'] = (complete_df['LotShape'] == 'Reg') * 1
complete_df = ohe(complete_df, 'LotShape')


# %% LandContour: Flatness of the property
#
#        Lvl  Near Flat/Level
#        Bnk  Banked - Quick and significant rise from street grade to building
#        HLS  Hillside - Significant slope from side to side
#        Low  Depression
#
# -> Counter({'Lvl': 2622, 'HLS': 120, 'Bnk': 115, 'Low': 59})
# -> So we can just transform this feature into a boolean one: IsContourLandLevel
complete_df['IsContourLandLevel'] = (complete_df['LandContour'] == 'Lvl') * 1
complete_df = ohe(complete_df, 'LandContour')


# %% Utilities: Type of utilities available
#
#        AllPub   All public Utilities (E,G,W,& S)
#        NoSewr   Electricity, Gas, and Water (Septic Tank)
#        NoSeWa   Electricity and Gas Only
#        ELO  Electricity only
#
# -> Counter({'AllPub': 2913, nan: 2, 'NoSeWa': 1})
# -> So it's an irrelevant feature, should be dropped all together
columns_to_drop.append('Utilities')


# %% LotConfig: Lot configuration
#
#        Inside   Inside lot
#        Corner   Corner lot
#        CulDSac  Cul-de-sac
#        FR2  Frontage on 2 sides of property
#        FR3  Frontage on 3 sides of property
#
complete_df = ohe(complete_df, 'LotConfig')


# %% LandSlope: Slope of property
#
#        Gtl  Gentle slope
#        Mod  Moderate Slope
#        Sev  Severe Slope
#
# -> Counter({'Gtl': 2776, 'Mod': 124, 'Sev': 16})
# -> So we can just transform this feature into a boolean one: IsSlopeGentle
complete_df['IsSlopeGentle'] = (complete_df['LandSlope'] == 'Gtl') * 1
complete_df = ohe(complete_df, 'LandSlope')

# columns_to_drop.append('LandSlope')


# %% Neighborhood: Physical locations within Ames city limits
#
#        Blmngtn  Bloomington Heights
#        Blueste  Bluestem
#        BrDale   Briardale
#        BrkSide  Brookside
#        ClearCr  Clear Creek
#        CollgCr  College Creek
#        Crawfor  Crawford
#        Edwards  Edwards
#        Gilbert  Gilbert
#        IDOTRR   Iowa DOT and Rail Road
#        MeadowV  Meadow Village
#        Mitchel  Mitchell
#        Names    North Ames
#        NoRidge  Northridge
#        NPkVill  Northpark Villa
#        NridgHt  Northridge Heights
#        NWAmes   Northwest Ames
#        OldTown  Old Town
#        SWISU    South & West of Iowa State University
#        Sawyer   Sawyer
#        SawyerW  Sawyer West
#        Somerst  Somerset
#        StoneBr  Stone Brook
#        Timber   Timberland
#        Veenker  Veenker
#
# -> According to other partecipants, the good neighborhoods are: 'NridgHt','Crawfor','StoneBr','Somerst','NoRidge'.
# -> Let's create a new boolean feature representing the belonging to one of these good neighborhoods.
complete_df['IsGoodNeighborhood'] = np.array([x in ('NridgHt', 'Crawfor', 'StoneBr', 'Somerst', 'NoRidge')
                                              for x in complete_df['Neighborhood']]) * 1
complete_df = ohe(complete_df, 'Neighborhood')

# columns_to_drop.append('Neighborhood')


# %% Condition1 && Condition2
#
# Condition1: Proximity to various conditions
#
#        Artery   Adjacent to arterial street
#        Feedr    Adjacent to feeder street
#        Norm Normal
#        RRNn Within 200' of North-South Railroad
#        RRAn Adjacent to North-South Railroad
#        PosN Near positive off-site feature--park, greenbelt, etc.
#        PosA Adjacent to postive off-site feature
#        RRNe Within 200' of East-West Railroad
#        RRAe Adjacent to East-West Railroad
#
#  Condition2: Proximity to various conditions (if more than one is present)
#
#        Artery   Adjacent to arterial street
#        Feedr    Adjacent to feeder street
#        Norm Normal
#        RRNn Within 200' of North-South Railroad
#        RRAn Adjacent to North-South Railroad
#        PosN Near positive off-site feature--park, greenbelt, etc.
#        PosA Adjacent to postive off-site feature
#        RRNe Within 200' of East-West Railroad
#        RRAe Adjacent to East-West Railroad
#
# -> We can merge these two features keeping in mind that 'Norm' means 'nothing particularly relevant is nearby'
# -> so we can ignore it when paired with some other condition.
# -> Furthermore there are ONLY 17 observations with more than 1 condition (both different than Norm)!
# -> Of those 17, only 14 all have the 'Feedr' condition, so we can discard that and keep only the other one of the pair
# -> Here are the last 3: {'PosA', 'Artery'} {'RRAn', 'Artery'} {'Artery', 'RRNn'}
# -> We can just remove 'Artery' from the pairs.
# -> Let's not forget it's a categorical feature.
def conditions_merge(row):
    conditions = {row['Condition1'], row['Condition2']}
    condition = 'Norm'
    conditions.discard('Norm')
    if len(conditions) == 2:
        conditions.discard('Feedr' if 'Feedr' in conditions else 'Artery')
        condition = conditions.pop()
    elif len(conditions) == 1:
        condition = conditions.pop()

    return condition


complete_df['Condition'] = complete_df.apply(conditions_merge, axis=1).replace(
    to_replace='Norm', value=NONE_VALUE, inplace=True)
complete_df = ohe(complete_df, 'Condition')
complete_df = ohe(complete_df, 'Condition1')
complete_df = ohe(complete_df, 'Condition2')

# columns_to_drop.extend(['Condition1', 'Condition2'])


# %% BldgType: Type of dwelling
#
#        1Fam Single-family Detached
#        2FmCon   Two-family Conversion; originally built as one-family dwelling
#        Duplx    Duplex
#        TwnhsE   Townhouse End Unit
#        TwnhsI   Townhouse Inside Unit
#
complete_df = ohe(complete_df, 'BldgType')


# %% HouseStyle: Style of dwelling
#
#        1Story   One story
#        1.5Fin   One and one-half story: 2nd level finished
#        1.5Unf   One and one-half story: 2nd level unfinished
#        2Story   Two story
#        2.5Fin   Two and one-half story: 2nd level finished
#        2.5Unf   Two and one-half story: 2nd level unfinished
#        SFoyer   Split Foyer
#        SLvl Split Level
#
# -> Might have an order!
# -> Some values not present in test, remove (after the OneHotEncoding) the column_value: {'2.5Fin'}
complete_df = ohe(complete_df, 'HouseStyle')
columns_to_drop.append('HouseStyle_2.5Fin')


# %% OverallQual: Rates the overall material and finish of the house
#
#        10   Very Excellent
#        9    Excellent
#        8    Very Good
#        7    Good
#        6    Above Average
#        5    Average
#        4    Below Average
#        3    Fair
#        2    Poor
#        1    Very Poor
#
# -> The distribution of these values shows that they can be grouped into 3 bins, meaning: bad - average - good
# -> Counter({5: 825, 6: 731, 7: 600, 8: 342, 4: 225, 9: 107, 3: 40, 10: 29, 2: 13, 1: 4})
bins_overall_qual = {range(1, 4): 1, range(4, 7): 2, range(7, 11): 3}


def overall_qual_simplify(row):
    qual = row['OverallQual']
    for bin, simple_qual in bins_overall_qual.items():
        if qual in bin:
            return simple_qual


complete_df['OverallQualSimplified'] = complete_df.apply(overall_qual_simplify, axis=1)
# columns_to_drop.append('OverallQual')


# %% OverallCond: Rates the overall condition of the house
#
#        10   Very Excellent
#        9    Excellent
#        8    Very Good
#        7    Good
#        6    Above Average
#        5    Average
#        4    Below Average
#        3    Fair
#        2    Poor
#        1    Very Poor
#
# -> The distribution of these values shows that they can be grouped into 3 bins, meaning: bad - average - good
# -> Counter({5: 1643, 6: 530, 7: 390, 8: 144, 4: 101, 3: 50, 9: 41, 2: 10, 1: 7})
bins_overall_cond = {range(1, 4): 1, range(4, 7): 2, range(7, 11): 3}


def overall_cond_simplify(row):
    qual = row['OverallCond']
    for bin, simple_qual in bins_overall_cond.items():
        if qual in bin:
            return simple_qual


complete_df['OverallCondSimplified'] = complete_df.apply(overall_cond_simplify, axis=1)
# columns_to_drop.append('OverallCond')


# %% YearBuilt && YearRemodAdd && YrSold
#
#  YearBuilt: Original construction date
#
#  YearRemodAdd: Remodel date (same as construction date if no remodeling or additions)
#
#  YrSold: Year Sold (YYYY)
#
# -> There's a lot going on here.
# -> First of all, we can bin the years of construction (going from 1872 to 2010, so spanning 128 years)
# -> into 7 ranges (to obtain ~20 years for each bin):
complete_df['YearBuiltBinned'] = pd.cut(complete_df['YearBuilt'], 7, labels=False)

# -> Now, we don't care about the exact remodel date, we just want to know if it has been remodeled:
complete_df['IsRemodeled'] = (complete_df['YearRemodAdd'] != complete_df['YearBuilt']) * 1

# -> Is the remodel a very recent one (same year of the sale)?
complete_df['IsRemodelRecent'] = (complete_df['YearRemodAdd'] == complete_df['YrSold']) * 1

# -> Is this house new (year of sale same as the year of construction)?
complete_df['IsNewHouse'] = (complete_df['YearBuilt'] == complete_df['YrSold']) * 1

# columns_to_drop.extend(['YearRemodAdd', 'YrSold', 'YearBuilt'])


# %% RoofStyle: Type of roof
#
#        Flat Flat
#        Gable    Gable
#        Gambrel  Gabrel (Barn)
#        Hip  Hip
#        Mansard  Mansard
#        Shed Shed
#
complete_df = ohe(complete_df, 'RoofStyle')


# %% RoofMatl: Roof material
#
#        ClyTile  Clay or Tile
#        CompShg  Standard (Composite) Shingle
#        Membran  Membrane
#        Metal    Metal
#        Roll Roll
#        Tar&Grv  Gravel & Tar
#        WdShake  Wood Shakes
#        WdShngl  Wood Shingles
#
# -> Some values not present in test, remove (after the OneHotEncoding) the column_value {'Roll', 'Metal', 'Membran'}
complete_df = ohe(complete_df, 'RoofMatl')
columns_to_drop.extend(["RoofMatl_{}".format(x) for x in ["Roll", "Metal", "Membran"]])


# %% Exterior1st && Exterior2nd
#
# Exterior1st: Exterior covering on house
#
#        AsbShng  Asbestos Shingles
#        AsphShn  Asphalt Shingles
#        BrkComm  Brick Common
#        BrkFace  Brick Face
#        CBlock   Cinder Block
#        CemntBd  Cement Board
#        HdBoard  Hard Board
#        ImStucc  Imitation Stucco
#        MetalSd  Metal Siding
#        Other    Other
#        Plywood  Plywood
#        PreCast  PreCast
#        Stone    Stone
#        Stucco   Stucco
#        VinylSd  Vinyl Siding
#        Wd Sdng  Wood Siding
#        WdShing  Wood Shingles
#
#  Exterior2nd: Exterior covering on house (if more than one material)
#
#        AsbShng  Asbestos Shingles
#        AsphShn  Asphalt Shingles
#        BrkComm  Brick Common
#        BrkFace  Brick Face
#        CBlock   Cinder Block
#        CemntBd  Cement Board
#        HdBoard  Hard Board
#        ImStucc  Imitation Stucco
#        MetalSd  Metal Siding
#        Other    Other
#        Plywood  Plywood
#        PreCast  PreCast
#        Stone    Stone
#        Stucco   Stucco
#        VinylSd  Vinyl Siding
#        Wd Sdng  Wood Siding
#        WdShing  Wood Shingles
#
# -> We can merge these two features after the first OHE,
# -> keeping in mind that we must assign 1 to the 2nd relevant column.
# -> There is also a misspell of some value 'CmentBd', 'Wd Shng' and 'Brk Cmn'
complete_df['Exterior1st'].replace(to_replace='CmentBd', value='CemntBd', inplace=True)
complete_df['Exterior2nd'].replace(to_replace='CmentBd', value='CemntBd', inplace=True)

complete_df['Exterior1st'].replace(to_replace='Wd Shng', value='Wd Sdng', inplace=True)
complete_df['Exterior2nd'].replace(to_replace='Wd Shng', value='Wd Sdng', inplace=True)

complete_df['Exterior1st'].replace(to_replace='Brk Cmn', value='BrkComm', inplace=True)
complete_df['Exterior2nd'].replace(to_replace='Brk Cmn', value='BrkComm', inplace=True)

complete_df['Exterior1st'].fillna("VinylSd", inplace=True)
complete_df['Exterior2nd'].fillna("VinylSd", inplace=True)

complete_df['Exterior'] = complete_df['Exterior1st']
complete_df = ohe(complete_df, 'Exterior')

complete_df['Exterior_Other'] = np.zeros((complete_df.shape[0], 1), dtype=np.int)

for i, name in enumerate(complete_df['Exterior2nd']):
    assert 'Exterior_{}'.format(name) in complete_df, 'Exterior_{}'.format(name)
    complete_df.loc[complete_df.index[i], 'Exterior_{}'.format(name)] = 1

complete_df = ohe(complete_df, 'Exterior1st')
complete_df = ohe(complete_df, 'Exterior2nd')

# columns_to_drop.extend(['Exterior1st', 'Exterior2nd'])
# print(complete_df[[x for x in complete_df if x.startswith('Exterior')]])


# %% MasVnrType && MasVnrArea
#
# MasVnrType: Masonry veneer type
#
#        BrkCmn   Brick Common
#        BrkFace  Brick Face
#        CBlock   Cinder Block
#        None None
#        Stone    Stone
#
#  MasVnrArea: Masonry veneer area in square feet
#
# -> First of all, if MasVnrArea is different than 0/NaN we can be sure that the house has a masonry veneer.
# -> The 'BrkFace' type is by large the most common one (after the 'None' type).
# -> So, for the MasVnrType feature, we fill NONE_VALUE when we don't get more info from the MasVnrArea,
# -> otherwise 'BrkFace'.
# -> Let's not forget that MasVnrType is a categorical feature.
complete_df["MasVnrArea"] = complete_df["MasVnrArea"].fillna(0).astype(int)
temp_df = complete_df[['MasVnrType', 'MasVnrArea']].copy()
indexes_to_fill = (complete_df['MasVnrArea'] != 0) & ((complete_df['MasVnrType'] == 'None') | (complete_df['MasVnrType']
                                                                                               .isnull()))
complete_df.loc[indexes_to_fill, 'MasVnrType'] = 'BrkFace'
complete_df['MasVnrType'].fillna(NONE_VALUE, inplace=True)
complete_df = ohe(complete_df, 'MasVnrType')


# %% ExterQual: Evaluates the quality of the material on the exterior
#
#        Ex   Excellent
#        Gd   Good
#        TA   Average/Typical
#        Fa   Fair
#        Po   Poor
#
# -> This is a categorical feature, but with an order which should be preserved!
# complete_df['ExterQual'] = complete_df['ExterQual'].map(qualities_dict).astype(int)
complete_df = ints_encoding(complete_df, 'ExterQual', qualities_dict)

# %% ExterCond: Evaluates the present condition of the material on the exterior
#
#        Ex   Excellent
#        Gd   Good
#        TA   Average/Typical
#        Fa   Fair
#        Po   Poor
#
# -> This is a categorical feature, but with an order which should be preserved!
complete_df = ints_encoding(complete_df, 'ExterCond', qualities_dict)


# %% Foundation: Type of foundation
#
#        BrkTil   Brick & Tile
#        CBlock   Cinder Block
#        PConc    Poured Contrete
#        Slab Slab
#        Stone    Stone
#        Wood Wood
#
complete_df = ohe(complete_df, 'Foundation')


# %% ~~~~~ Remove inconsistencies from Bsmt columns ~~~~~
complete_df.loc[332, 'BsmtFinType2'] = 'ALQ'
complete_df.loc[947, 'BsmtExposure'] = 'No'
complete_df.loc[1485, 'BsmtExposure'] = 'No'
complete_df.loc[2038, 'BsmtCond'] = 'TA'
complete_df.loc[2183, 'BsmtCond'] = 'TA'
complete_df.loc[2215, 'BsmtQual'] = 'Po'
complete_df.loc[2216, 'BsmtQual'] = 'Fa'
complete_df.loc[2346, 'BsmtExposure'] = 'No'
complete_df.loc[2522, 'BsmtCond'] = 'Gd'

# %% BsmtQual: Evaluates the height of the basement
#
#        Ex   Excellent (100+ inches)
#        Gd   Good (90-99 inches)
#        TA   Typical (80-89 inches)
#        Fa   Fair (70-79 inches)
#        Po   Poor (<70 inches
#        NA   No Basement
#
qualities_dict_custom = {NONE_VALUE: 0, 'Po': 3, 'Fa': 2, 'TA': 3, 'Gd': 4, 'Ex': 5}
complete_df['BsmtQual'] = complete_df['BsmtQual'].fillna(NONE_VALUE)
complete_df = ints_encoding(complete_df, 'BsmtQual', qualities_dict_custom)


# %% BsmtCond: Evaluates the general condition of the basement
#
#        Ex   Excellent
#        Gd   Good
#        TA   Typical - slight dampness allowed
#        Fa   Fair - dampness or some cracking or settling
#        Po   Poor - Severe cracking, settling, or wetness
#        NA   No Basement
#
complete_df['BsmtCond'] = complete_df['BsmtCond'].fillna(NONE_VALUE)
complete_df = ints_encoding(complete_df, 'BsmtCond', qualities_dict)


# %% BsmtExposure: Refers to walkout or garden level walls
#
#        Gd   Good Exposure
#        Av   Average Exposure (split levels or foyers typically score average or above)
#        Mn   Mimimum Exposure
#        No   No Exposure
#        NA   No Basement
#
# -> TODO Gestisci differenza fra No e NA (?)
complete_df['BsmtExposure'] = complete_df['BsmtExposure'].fillna(NONE_VALUE)
complete_df = ints_encoding(complete_df, 'BsmtExposure', {NONE_VALUE: 0, 'No': 1, 'Mn': 2, 'Av': 3, 'Gd': 4})


# %% BsmtFinType1: Rating of basement finished area
#
#        GLQ  Good Living Quarters
#        ALQ  Average Living Quarters
#        BLQ  Below Average Living Quarters
#        Rec  Average Rec Room
#        LwQ  Low Quality
#        Unf  Unfinshed
#        NA   No Basement
#
complete_df['BsmtFinType1'] = complete_df['BsmtFinType1'].fillna(NONE_VALUE)
complete_df = ints_encoding(complete_df, 'BsmtFinType1', fin_qualities_dict)


# %% BsmtFinSF1: Type 1 finished square feet
#
complete_df['BsmtFinSF1'] = complete_df['BsmtFinSF1'].fillna(0).astype(int)


# %% BsmtFinType2: Rating of basement finished area (if multiple types)
#
#        GLQ  Good Living Quarters
#        ALQ  Average Living Quarters
#        BLQ  Below Average Living Quarters
#        Rec  Average Rec Room
#        LwQ  Low Quality
#        Unf  Unfinshed
#        NA   No Basement
#
complete_df['BsmtFinType2'] = complete_df['BsmtFinType2'].fillna(NONE_VALUE)
complete_df = ints_encoding(complete_df, 'BsmtFinType2', fin_qualities_dict)


# %% BsmtFinSF2: Type 2 finished square feet
#
complete_df['BsmtFinSF2'] = complete_df['BsmtFinSF2'].fillna(0).astype(int)


# %% BsmtUnfSF: Unfinished square feet of basement area
#
complete_df['BsmtUnfSF'] = complete_df['BsmtUnfSF'].fillna(0).astype(int)


# %% TotalBsmtSF: Total square feet of basement area
#
complete_df['TotalBsmtSF'] = complete_df['TotalBsmtSF'].fillna(0).astype(int)
complete_df['BsmtIsPresent'] = complete_df['TotalBsmtSF'].apply(lambda x: 1 if x > 0 else 0)


# %% Heating: Type of heating
#
#        Floor    Floor Furnace
#        GasA Gas forced warm air furnace
#        GasW Gas hot water or steam heat
#        Grav Gravity furnace
#        OthW Hot water or steam heat other than gas
#        Wall Wall furnace
#
# -> Some values not present in test, remove (after the OneHotEncoding) the column_value {'Floor', 'OthW'}
complete_df = ohe(complete_df, 'Heating')
columns_to_drop.extend(["Heating_{}".format(x) for x in ["Floor", "OthW"]])


# %% HeatingQC: Heating quality and condition
#
#        Ex   Excellent
#        Gd   Good
#        TA   Average/Typical
#        Fa   Fair
#        Po   Poor
#
complete_df = ints_encoding(complete_df, 'HeatingQC', qualities_dict)


# %% CentralAir: Central air conditioning
#
#        N    No
#        Y    Yes
#
# complete_df['HasCentralAir'] = (complete_df['CentralAir'] == 'Y') * 1 todo i booleano vanno one hot encoded?
complete_df = ohe(complete_df, 'CentralAir')


# %% Electrical: Electrical system
#
#        SBrkr    Standard Circuit Breakers & Romex
#        FuseA    Fuse Box over 60 AMP and all Romex wiring (Average)
#        FuseF    60 AMP Fuse Box and mostly Romex wiring (Fair)
#        FuseP    60 AMP Fuse Box and mostly knob & tube wiring (poor)
#        Mix  Mixed
#
# -> Counter({'SBrkr': 2668, 'FuseA': 188, 'FuseF': 50, 'FuseP': 8, 'Mix': 1, nan: 1})
# -> Therefore, we can set the only NaN value to 'SBrkr' which is by far the most common one.
# -> Some values not present in test, remove (after the OneHotEncoding) the column_value {'Mix'}
complete_df['Electrical'] = complete_df['Electrical'].fillna('SBrkr')
complete_df = ohe(complete_df, 'Electrical')
columns_to_drop.append('Electrical_Mix')


# %% 1stFlrSF: First Floor square feet
#


# %% 2ndFlrSF: Second floor square feet
#
complete_df['2ndFloorIsPresent'] = (complete_df['2ndFlrSF'] > 0) * 1


# %% LowQualFinSF: Low quality finished square feet (all floors)
#


# %% GrLivArea: Above grade (ground) living area square feet
#


# %% BsmtFullBath: Basement full bathrooms
#
complete_df['BsmtFullBath'] = complete_df['BsmtFullBath'].fillna(0).astype(int)


# %% BsmtHalfBath: Basement half bathrooms
#
complete_df['BsmtHalfBath'] = complete_df['BsmtHalfBath'].fillna(0).astype(int)


# %% FullBath: Full bathrooms above grade
#


# %% HalfBath: Half baths above grade
#


# %% Bedroom: Bedrooms above grade (does NOT include basement bedrooms)
#


# %% Kitchen: Kitchens above grade
#


# %% KitchenQual: Kitchen quality
#
#        Ex   Excellent
#        Gd   Good
#        TA   Typical/Average
#        Fa   Fair
#        Po   Poor
#
# -> Counter({'TA': 1492, 'Gd': 1150, 'Ex': 203, 'Fa': 70, nan: 1})
# -> Let's fill the single NaN value with the most common one (that also stands for 'average'!)
complete_df['KitchenQual'] = complete_df['KitchenQual'].fillna('TA')
complete_df = ints_encoding(complete_df, 'KitchenQual', qualities_dict)


# %% TotRmsAbvGrd: Total rooms above grade (does not include bathrooms)
#


# %% Functional: Home functionality (Assume typical unless deductions are warranted)
#
#        Typ  Typical Functionality
#        Min1 Minor Deductions 1
#        Min2 Minor Deductions 2
#        Mod  Moderate Deductions
#        Maj1 Major Deductions 1
#        Maj2 Major Deductions 2
#        Sev  Severely Damaged
#        Sal  Salvage only
#
# -> This is a categorical feature, but with order! (higher value means more functionalities)
# -> Counter({'Typ': 2715, 'Min2': 70, 'Min1': 64, 'Mod': 35, 'Maj1': 19, 'Maj2': 9, 'Sev': 2, nan: 2})
# -> Let's assume that the NaN values here are 'Typ' (that also stands for 'typical'!)
complete_df['Functional'] = complete_df['Functional'].fillna('Typ')
complete_df = ints_encoding(complete_df, 'Functional',  {NONE_VALUE: 0, 'Sal': 1, 'Sev': 2, 'Maj2': 3, 'Maj1': 4, 'Mod': 5, 'Min2': 6, 'Min1': 7, 'Typ': 8})


# %% Fireplaces && FireplaceQu
#
# Fireplaces: Number of fireplaces
#
# -> Counter({0: 1420, 1: 1267, 2: 218, 3: 10, 4: 1})
#
# FireplaceQu: Fireplace quality
#
#        Ex   Excellent - Exceptional Masonry Fireplace
#        Gd   Good - Masonry Fireplace in main level
#        TA   Average - Prefabricated Fireplace in main living area or Masonry Fireplace in basement
#        Fa   Fair - Prefabricated Fireplace in basement
#        Po   Poor - Ben Franklin Stove
#        NA   No Fireplace
# -> Counter({nan: 1420, 'Gd': 741, 'TA': 592, 'Fa': 74, 'Po': 46, 'Ex': 43})
# -> First, let's simplify the 'Fireplaces' feature into a boolean one
complete_df['FireplaceIsPresent'] = (complete_df['Fireplaces'] > 0) * 1
# -> Now, let's map the NaN values of 'FireplaceQu' to NONE_VALUE,
#    which will be mapped to 0 meaning there's no fireplace.
# -> We can do this since the rows with false 'HasFireplaces' are the same with NaN 'FireplaceQu'!
complete_df['FireplaceQu'] = complete_df['FireplaceQu'].fillna(NONE_VALUE)
complete_df = ints_encoding(complete_df, 'FireplaceQu', qualities_dict)

# TODO Here 'FA' means that there's a fireplace in the basement, so THERE IS A BASEMENT. Check for collisions!


# %% GarageType: Garage location
#
#        2Types   More than one type of garage
#        Attchd   Attached to home
#        Basment  Basement Garage
#        BuiltIn  Built-In (Garage part of house - typically has room above garage)
#        CarPort  Car Port
#        Detchd   Detached from home
#        NA   No Garage
#
complete_df["GarageType"].fillna(NONE_VALUE, inplace=True)
complete_df = ohe(complete_df, 'GarageType')


# %% GarageYrBlt: Year garage was built
#
complete_df.loc[2124, 'GarageYrBlt'] = complete_df['GarageYrBlt'].median()
complete_df.loc[2574, 'GarageYrBlt'] = complete_df['GarageYrBlt'].median()
complete_df.loc[2590, 'GarageYrBlt'] = 2007
complete_df["GarageYrBlt"] = complete_df["GarageYrBlt"].fillna(0).astype(float)
complete_df["GarageIsPresent"] = (complete_df["GarageYrBlt"] > 0) * 1
# columns_to_drop.append("GarageYrBlt")


# %% GarageFinish: Interior finish of the garage
#
#        Fin  Finished
#        RFn  Rough Finished
#        Unf  Unfinished
#        NA   No Garage
#
complete_df.loc[2124, 'GarageFinish'] = complete_df['GarageFinish'].mode()[0]
complete_df.loc[2574, 'GarageFinish'] = complete_df['GarageFinish'].mode()[0]
complete_df["GarageFinish"].fillna(NONE_VALUE, inplace=True)
complete_df = ints_encoding(complete_df, 'GarageFinish', {NONE_VALUE: 0, "Unf": 1, "RFn": 2, "Fin": 3})


# %% GarageCars: Size of garage in car capacity
#
complete_df.loc[2574, 'GarageCars'] = complete_df['GarageCars'].median()
complete_df["GarageCars"] = complete_df["GarageCars"].fillna(0).astype(int)


# %% GarageArea: Size of garage in square feet
#
complete_df.loc[2124, 'GarageArea'] = complete_df['GarageArea'].median()
complete_df.loc[2574, 'GarageArea'] = complete_df['GarageArea'].median()
complete_df["GarageArea"] = complete_df["GarageArea"].fillna(0).astype(int)


# %% GarageQual: Garage quality
#
#        Ex   Excellent
#        Gd   Good
#        TA   Typical/Average
#        Fa   Fair
#        Po   Poor
#        NA   No Garage
#
complete_df.loc[2124, 'GarageQual'] = complete_df['GarageQual'].mode()[0]
complete_df.loc[2574, 'GarageQual'] = complete_df['GarageQual'].mode()[0]
complete_df["GarageQual"].fillna(NONE_VALUE, inplace=True)
complete_df = ints_encoding(complete_df, 'GarageQual', qualities_dict)


# %% GarageCond: Garage condition
#
#        Ex   Excellent
#        Gd   Good
#        TA   Typical/Average
#        Fa   Fair
#        Po   Poor
#        NA   No Garage
#
complete_df.loc[2124, 'GarageCond'] = complete_df['GarageCond'].mode()[0]
complete_df.loc[2574, 'GarageCond'] = complete_df['GarageCond'].mode()[0]
complete_df["GarageCond"].fillna(NONE_VALUE, inplace=True)
complete_df = ints_encoding(complete_df, 'GarageCond', qualities_dict)


# %% PavedDrive: Paved driveway
#
#        Y    Paved
#        P    Partial Pavement
#        N    Dirt/Gravel
#
# -> Counter({'Y': 2638, 'N': 216, 'P': 62})
# -> Let's create a new boolean feature with the meaning 'has a paved drive?'
complete_df['HasPavedDrive'] = (complete_df['PavedDrive'] == 'Y') * 1
complete_df = ohe(complete_df, 'PavedDrive')

# columns_to_drop.append('PavedDrive')

# %% WoodDeckSF: Wood deck area in square feet
#


# %% OpenPorchSF: Open porch area in square feet
#


# %% EnclosedPorch: Enclosed porch area in square feet
#


# %% 3SsnPorch: Three season porch area in square feet
#


# %% ScreenPorch: Screen porch area in square feet
#


# %% PoolArea && PoolQC
# PoolArea: Pool area in square feet
#
# PoolQC: Pool quality
#
#        Ex   Excellent
#        Gd   Good
#        TA   Average/Typical
#        Fa   Fair
#        NA   No Pool
#
# Counter({0: 2904, 512: 1, 648: 1, 576: 1, 555: 1, 519: 1, 738: 1, 144: 1, 368: 1, 444: 1, 228: 1, 561: 1, 800: 1})
# PoolQC: Pool quality
# Counter({nan: 2907, 'Ex': 4, 'Gd': 3, 'Fa': 2})
# Let's just merge those two features into a simple 'has a pool?'
complete_df.loc[2418, 'PoolQC'] = 'Fa'
complete_df.loc[2501, 'PoolQC'] = 'Gd'
complete_df.loc[2597, 'PoolQC'] = 'Fa'
complete_df['PoolQC'].fillna(NONE_VALUE, inplace=True)
complete_df = ints_encoding(complete_df, 'PoolQC', {NONE_VALUE: 0, 'Fa': 1, 'TA': 2, 'Gd': 3, 'Ex': 4})
complete_df['PollIsPresent'] = (complete_df['PoolArea'] > 0) * 1

# columns_to_drop.extend(['PoolArea', 'PoolQC']) # TODO una casa con una megapiscina vale sicuro di più


# %% Fence: Fence quality
#
#        GdPrv    Good Privacy
#        MnPrv    Minimum Privacy
#        GdWo Good Wood
#        MnWw Minimum Wood/Wire
#        NA   No Fence
#
# -> This is a categorical feature, but with order! (higher value means better fence)
# -> Counter({nan: 2345, 'MnPrv': 329, 'GdPrv': 118, 'GdWo': 112, 'MnWw': 12})
# -> Let's map the NaN values to NONE_VALUE which will then be mapped to a 0 quality.
complete_df['Fence'].fillna(NONE_VALUE, inplace=True)
complete_df = ints_encoding(complete_df, 'Fence', {NONE_VALUE: 0, 'MnWw': 1, 'GdWo': 2, 'MnPrv': 3, 'GdPrv': 4})


# %% MiscFeature && MiscVal
#
#  MiscFeature: Miscellaneous feature not covered in other categories
#
#        Elev Elevator
#        Gar2 2nd Garage (if not described in garage section)
#        Othr Other
#        Shed Shed (over 100 SF)
#        TenC Tennis Court
#        NA   None
#
#  MiscVal: $Value of miscellaneous feature
#
# -> Counter({nan: 2811, 'Shed': 95, 'Gar2': 5, 'Othr': 4, 'TenC': 1})
# -> MiscVal: $Value of miscellaneous feature
# -> Given this distribution, we can assume that the only useful info in this feature is the presence of a shed.
# -> Let's create a boolean feature representing that keeping in mind the value of MiscVal that could be 0 (no shed!).
def has_shed(row):
    # assert (row['MiscFeature'] == 'Shed' and row['MiscVal'] > 0)*1 in (0, 1)
    return (row['MiscFeature'] == 'Shed' and row['MiscVal'] > 0) * 1


complete_df['HasShed'] = complete_df.apply(has_shed, axis=1)

complete_df['MiscFeature'].fillna(NONE_VALUE, inplace=True)
complete_df = ohe(complete_df, 'MiscFeature')

# columns_to_drop.extend(['MiscFeature', 'MiscVal'])


# %% MoSold: Month Sold (MM)
#
complete_df['MoSold'] = complete_df['MoSold'].astype(int)


# %% SaleType: Type of sale
#
#        WD   Warranty Deed - Conventional
#        CWD  Warranty Deed - Cash
#        VWD  Warranty Deed - VA Loan
#        New  Home just constructed and sold
#        COD  Court Officer Deed/Estate
#        Con  Contract 15% Down payment regular terms
#        ConLw    Contract Low Down payment and low interest
#        ConLI    Contract Low Interest
#        ConLD    Contract Low Down
#        Oth  Other
#
# -> Counter({'WD': 2524, 'New': 237, 'COD': 87, 'ConLD': 26, 'CWD': 12, 'ConLI': 9, 'ConLw': 8, 'Oth': 7,
# -> 'Con': 5, nan: 1})
# -> Let's fill the single NaN value to the most common one (WD)
complete_df['SaleType'] = complete_df['SaleType'].fillna('WD')
complete_df = ints_encoding(complete_df, 'SaleType', {'WD': 9, 'CWD': 8, 'VWD': 7, 'New': 6, 'COD': 5, 'Con': 4, 'ConLw': 3, 'ConLI': 2, 'ConLD': 1, 'Oth': 0})


# %% SaleCondition: Condition of sale
#
#        Normal   Normal Sale
#        Abnorml  Abnormal Sale -  trade, foreclosure, short sale
#        AdjLand  Adjoining Land Purchase
#        Alloca   Allocation - two linked properties with separate deeds, typically condo with a garage unit
#        Family   Sale between family members
#        Partial  Home was not completed when last assessed (associated with New Homes)
complete_df = ohe(complete_df, 'SaleCondition')


# ~~~~~ Resolve skewness ~~~~ TODO camuffa codice
from scipy.stats import skew

numeric_features = ["MiscVal",
                    "PoolArea",
                    "LotArea",
                    "LowQualFinSF",
                    "3SsnPorch",
                    "KitchenAbvGr",
                    "BsmtFinSF2",
                    "EnclosedPorch",
                    "ScreenPorch",
                    "BsmtHalfBath",
                    "MasVnrArea",
                    "OpenPorchSF",
                    "WoodDeckSF",
                    "1stFlrSF",
                    "LotFrontage",
                    "GrLivArea",
                    "BsmtFinSF1",
                    "BsmtUnfSF",
                    "2ndFlrSF",
                    "TotRmsAbvGrd",
                    "Fireplaces",
                    "HalfBath",
                    "TotalBsmtSF",
                    "BsmtFullBath",
                    "OverallCond",
                    "BedroomAbvGr",
                    "GarageArea",
                    "MoSold",
                    "OverallQual",
                    "FullBath",
                    "YrSold",
                    "GarageCars",
                    "YearRemodAdd",
                    "YearBuilt",
                    "GarageYrBlt"]

# for y in numeric_features:
#     print(complete_df[y].dtype)

skew_features = complete_df[numeric_features].apply(lambda x: skew(x)).sort_values(ascending=False)
skews = pd.DataFrame({'skew': skew_features})

# print(skew_features)

from scipy.special import boxcox1p
from scipy.stats import boxcox_normmax

high_skew = skew_features[skew_features > 0.5]
high_skew = high_skew
skew_index = high_skew.index

for i in skew_index:
    complete_df[i] = boxcox1p(complete_df[i], boxcox_normmax(complete_df[i] + 1))

# Check it is adjusted
# skew_features2 = complete_df[numeric_features].apply(lambda x: skew(x)).sort_values(ascending=False)
# skews2 = pd.DataFrame({'skew': skew_features2})
# print(skew_features2)


# ~~~~~ ADD NEW FEATURES ~~~~

# %% TotalSF
# We can build a new feature from those two and the basement info: the total area of the two floors + the basement
complete_df['TotalSF'] = complete_df['1stFlrSF'] + complete_df['2ndFlrSF'] + complete_df['TotalBsmtSF']


# %% TotalArea
area_cols = ['LotFrontage', 'LotArea', 'MasVnrArea', 'BsmtFinSF1', 'BsmtFinSF2', 'BsmtUnfSF',
             'TotalBsmtSF', '1stFlrSF', '2ndFlrSF', 'GrLivArea', 'GarageArea', 'WoodDeckSF',
             'OpenPorchSF', 'EnclosedPorch', '3SsnPorch', 'ScreenPorch', 'LowQualFinSF', 'PoolArea']
complete_df['TotalArea'] = complete_df[area_cols].sum(axis=1)

# %% Total_sqr_footage
complete_df['Total_sqr_footage'] = (complete_df['BsmtFinSF1'] + complete_df['BsmtFinSF2'] +
                                 complete_df['1stFlrSF'] + complete_df['2ndFlrSF'])

# %% Total_Bathrooms
complete_df['Total_Bathrooms'] = (complete_df['FullBath'] + (0.5*complete_df['HalfBath']) +
                               complete_df['BsmtFullBath'] + (0.5*complete_df['BsmtHalfBath']))

# %% Total_porch_sf
complete_df['Total_porch_sf'] = (complete_df['OpenPorchSF'] + complete_df['3SsnPorch'] +
                              complete_df['EnclosedPorch'] + complete_df['ScreenPorch'] +
                             complete_df['WoodDeckSF'])


# %% Dropping bad features
out = ['MSSubClass_150',
       # "BsmtQual_Po", # TODO: se non usiamo l'ordinamento va messa!
        'MSZoning_C (all)']
columns_to_drop.extend(out)

# ~~~~~ REMOVE FEATURES ~~~~
for x in columns_to_drop:
    assert x in complete_df, "Trying to drop {}, but it isn't in the df".format(x)
complete_df.drop(columns=columns_to_drop, inplace=True)


# TODO We should remove discordant data (there can't be a single basement-feature with a 'no basement' meaning if at least another one is present
# TODO We should remove discordant data (there can't be a single garage-feature with a 'no garage' meaning if at least another one is present


# %% Check for missing values
nulls = np.sum(complete_df.isnull())
nullcols = nulls.loc[(nulls != 0)]
dtypes = complete_df.dtypes
dtypes2 = dtypes.loc[(nulls != 0)]
info = pd.concat([nullcols, dtypes2], axis=1).sort_values(by=0, ascending=False)
# print(info)
print("There are", len(nullcols), "columns with missing values")


# %% Infos
# print(complete_df.info(verbose=True))
# print(complete_df.info(verbose=False))


# %% ~~~~~ Split again into train and test ~~~~~
x_train = complete_df[:train_len]
x_test = complete_df[train_len:]
assert train_len == x_train.shape[0]
assert test_len == x_test.shape[0]


# %% ~~~~~ Check shapes ~~~~~
# print(x_train.shape)
# print(y_train.shape)
# print(x_test.shape)


def get_engineered_train_test():
    return (train_ids, x_train, y_train), (test_ids, x_test)