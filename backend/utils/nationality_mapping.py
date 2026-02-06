
COUNTRY_TO_DEMONYM = {
    # East Africa
    'Uganda': 'Ugandan',
    'Kenya': 'Kenyan',
    'Tanzania': 'Tanzanian',
    'Rwanda': 'Rwandan',
    'Burundi': 'Burundian',
    'South Sudan': 'South Sudanese',
    'DR Congo': 'Congolese',
    'Ethiopia': 'Ethiopian',
    'Somalia': 'Somali',
    'Eritrea': 'Eritrean',
    'Djibouti': 'Djiboutian',
    'Sudan': 'Sudanese',
    
    # Rest of Africa
    'Nigeria': 'Nigerian',
    'Ghana': 'Ghanaian',
    'South Africa': 'South African',
    'Zambia': 'Zambian',
    'Zimbabwe': 'Zimbabwean',
    'Malawi': 'Malawian',
    'Mozambique': 'Mozambican',
    'Angola': 'Angolan',
    'Botswana': 'Motswana',
    'Namibia': 'Namibian',
    'Eswatini': 'Swazi',
    'Lesotho': 'Mosotho',
    'Madagascar': 'Malagasy',
    'Mauritius': 'Mauritian',
    'Seychelles': 'Seychellois',
    'Comoros': 'Comorian',
    'Cameroon': 'Cameroonian',
    'Gabon': 'Gabonese',
    'Congo': 'Congolese',
    'Central African Republic': 'Central African',
    'Chad': 'Chadian',
    'Niger': 'Nigerien',
    'Mali': 'Malian',
    'Burkina Faso': 'Burkinabé',
    'Senegal': 'Senegalese',
    'Gambia': 'Gambian',
    'Guinea-Bissau': 'Bissau-Guinean',
    'Guinea': 'Guinean',
    'Sierra Leone': 'Sierra Leonean',
    'Liberia': 'Liberian',
    "Côte d'Ivoire": 'Ivorian',
    'Togo': 'Togolese',
    'Benin': 'Beninese',
    'Mauritania': 'Mauritanian',
    'Egypt': 'Egyptian',
    'Libya': 'Libyan',
    'Tunisia': 'Tunisian',
    'Algeria': 'Algerian',
    'Morocco': 'Moroccan',
    
    # International
    'United States': 'American',
    'United Kingdom': 'British',
    'India': 'Indian',
    'China': 'Chinese',
    'Pakistan': 'Pakistani',
    'Bangladesh': 'Bangladeshi',
}

def get_demonym(country_name):
    """
    Get the demonym for a given country name.
    """
    if not country_name:
        return 'Ugandan'  # Default to Ugandan if not provided
        
    return COUNTRY_TO_DEMONYM.get(country_name, country_name)
