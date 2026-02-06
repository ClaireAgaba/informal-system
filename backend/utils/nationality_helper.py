"""
Utility functions for handling nationality/country conversions
"""

# Mapping from ISO 3166-1 alpha-2 country codes to nationality demonyms
COUNTRY_CODE_TO_DEMONYM = {
    # East Africa
    'UG': 'Ugandan',
    'KE': 'Kenyan',
    'TZ': 'Tanzanian',
    'RW': 'Rwandan',
    'BI': 'Burundian',
    'SS': 'South Sudanese',
    'CD': 'Congolese',
    'ET': 'Ethiopian',
    'SO': 'Somali',
    'ER': 'Eritrean',
    'DJ': 'Djiboutian',
    'SD': 'Sudanese',
    
    # Rest of Africa
    'NG': 'Nigerian',
    'GH': 'Ghanaian',
    'ZA': 'South African',
    'ZM': 'Zambian',
    'ZW': 'Zimbabwean',
    'MW': 'Malawian',
    'MZ': 'Mozambican',
    'AO': 'Angolan',
    'BW': 'Motswana',
    'NA': 'Namibian',
    'SZ': 'Swazi',
    'LS': 'Mosotho',
    'MG': 'Malagasy',
    'MU': 'Mauritian',
    'SC': 'Seychellois',
    'KM': 'Comorian',
    'CM': 'Cameroonian',
    'GA': 'Gabonese',
    'CG': 'Congolese',
    'CF': 'Central African',
    'TD': 'Chadian',
    'NE': 'Nigerien',
    'ML': 'Malian',
    'BF': 'Burkinabé',
    'SN': 'Senegalese',
    'GM': 'Gambian',
    'GW': 'Bissau-Guinean',
    'GN': 'Guinean',
    'SL': 'Sierra Leonean',
    'LR': 'Liberian',
    'CI': 'Ivorian',
    'TG': 'Togolese',
    'BJ': 'Beninese',
    'MR': 'Mauritanian',
    'EG': 'Egyptian',
    'LY': 'Libyan',
    'TN': 'Tunisian',
    'DZ': 'Algerian',
    'MA': 'Moroccan',
    
    # International
    'US': 'American',
    'GB': 'British',
    'IN': 'Indian',
    'CN': 'Chinese',
    'PK': 'Pakistani',
    'BD': 'Bangladeshi',
}


def get_nationality_from_country(country_code):
    """
    Get the nationality demonym for a given country code.
    
    Args:
        country_code: ISO 3166-1 alpha-2 country code (e.g., 'TZ', 'UG')
        
    Returns:
        str: Nationality demonym (e.g., 'Tanzanian', 'Ugandan')
             Returns 'Ugandan' as default if country code not found
    """
    if not country_code:
        return 'Ugandan'
    
    # Convert to string in case it's a Country object
    code = str(country_code).upper()
    
    return COUNTRY_CODE_TO_DEMONYM.get(code, 'Ugandan')
