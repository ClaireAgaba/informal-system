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
    'AF': 'Afghan',
    'AE': 'Emirati',
    'SA': 'Saudi',
    'QA': 'Qatari',
    'TR': 'Turkish',
    'IR': 'Iranian',
    'IQ': 'Iraqi',
    'SY': 'Syrian',
    'LB': 'Lebanese',
    'JO': 'Jordanian',
    'IL': 'Israeli',
    'MY': 'Malaysian',
    'ID': 'Indonesian',
    'PH': 'Filipino',
    'VN': 'Vietnamese',
    'TH': 'Thai',
    'JP': 'Japanese',
    'KR': 'South Korean',
    'AU': 'Australian',
    'NZ': 'New Zealander',
    'CA': 'Canadian',
    'MX': 'Mexican',
    'BR': 'Brazilian',
    'AR': 'Argentine',
    'CO': 'Colombian',
    'PE': 'Peruvian',
    'VE': 'Venezuelan',
    'CL': 'Chilean',
    'RU': 'Russian',
    'UA': 'Ukrainian',
    'BY': 'Belarusian',
    'PL': 'Polish',
    'DE': 'German',
    'FR': 'French',
    'IT': 'Italian',
    'ES': 'Spanish',
    'PT': 'Portuguese',
    'NL': 'Dutch',
    'BE': 'Belgian',
    'CH': 'Swiss',
    'AT': 'Austrian',
    'SE': 'Swedish',
    'NO': 'Norwegian',
    'DK': 'Danish',
    'FI': 'Finnish',
    'IE': 'Irish',
    'GR': 'Greek',
}


def get_nationality_from_country(country_code):
    """
    Get the nationality demonym for a given country code.
    
    Args:
        country_code: ISO 3166-1 alpha-2 country code (e.g., 'TZ', 'UG')
        
    Returns:
        str: Nationality demonym (e.g., 'Tanzanian', 'Ugandan')
             Returns the country name if demonym not found, or 'Ugandan' as fallback
    """
    if not country_code:
        return 'Ugandan'
    
    # Convert to string in case it's a Country object
    code = str(country_code).upper()
    
    # Return demonym if we have a mapping
    if code in COUNTRY_CODE_TO_DEMONYM:
        return COUNTRY_CODE_TO_DEMONYM[code]
        
    # If it's a Country object from django-countries, it has a name property
    if hasattr(country_code, 'name') and country_code.name:
        return country_code.name
        
    # If passed as a string code, try to resolve it using django-countries
    try:
        from django_countries import countries
        country_name = dict(countries).get(code)
        if country_name:
            return str(country_name)
    except ImportError:
        pass
        
    return 'Ugandan'
