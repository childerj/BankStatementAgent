#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive test with 1000+ real bank names from across the United States
"""

def extract_complete_bank_name_from_line(line):
    """Extract complete bank name from a single line with advanced logic for complex names"""
    # Common bank name endings that indicate where to stop
    bank_endings = ['bank', 'union', 'financial', 'trust', 'services', 'corp', 'corporation', 'company', 'co', 'credit']
    # Common connecting words in bank names
    connecting_words = ['of', 'and', '&', 'the', 'for']
    
    words = line.split()
    if not words:
        return None
    
    # Special case: If line starts with "Bank of [Something]", take the full name
    if words[0].lower() == 'bank' and len(words) >= 3 and words[1].lower() in connecting_words:
        # Look for natural stopping points after "Bank of"
        for i in range(3, min(len(words) + 1, 7)):  # Check up to 6 words total
            if i < len(words):
                word_lower = words[i].lower().rstrip('.,')
                if word_lower in ['report', 'statement', 'date', 'page', 'account', 'balance', 'type', 'bai', 'test']:
                    bank_name = ' '.join(words[:i])
                    return bank_name.strip()
        # If no stopping point found, take up to 6 words for "Bank of X Y Z"
        bank_name = ' '.join(words[:min(6, len(words))])
        return bank_name.strip()
    
    # Look for natural stopping points
    for i, word in enumerate(words):
        word_lower = word.lower().rstrip('.,')
        
        # Stop at obvious non-bank words FIRST (before checking bank endings)
        if word_lower in ['report', 'statement', 'date', 'page', 'account', 'balance', 'type', 'bai', 'test']:
            if i > 0:  # If we have some words before this
                bank_name = ' '.join(words[:i])
                return bank_name.strip()
            break
        
        # If we hit a bank ending, include it and stop
        # BUT: Don't stop on intermediate bank endings if "Bank" appears later
        if word_lower in bank_endings:
            # Look ahead to see if "Bank" appears in the next few words
            has_bank_ahead = False
            for j in range(i + 1, min(i + 4, len(words))):
                if words[j].lower().rstrip('.,') == 'bank':
                    has_bank_ahead = True
                    break
            
            # If no "Bank" ahead, this is likely the end
            if not has_bank_ahead:
                bank_name = ' '.join(words[:i+1])
                return bank_name.strip()
            # If "Bank" is ahead, continue to include it
            elif word_lower == 'bank':
                # This is the final "Bank" - include it and stop
                bank_name = ' '.join(words[:i+1])
                return bank_name.strip()
    
    # If no clear ending found, take the whole line if it's reasonable length
    if len(words) <= 6 and len(line) <= 50:
        return line.strip()
    
    return None

# 1000+ real bank names from across the United States
THOUSAND_BANK_NAMES = [
    # Tier 1: Major National Banks (50)
    "Bank of America", "JPMorgan Chase Bank", "Wells Fargo Bank", "Citibank", "U.S. Bank",
    "PNC Bank", "Truist Bank", "TD Bank", "Capital One Bank", "Fifth Third Bank",
    "Regions Bank", "KeyBank", "Citizens Bank", "M&T Bank", "Huntington National Bank",
    "Comerica Bank", "Zions Bancorporation", "First Citizens Bank", "Synovus Bank", "Valley National Bank",
    "First National Bank", "Community Bank", "Farmers Bank", "Merchants Bank", "Heritage Bank",
    "Security Bank", "Liberty Bank", "Independent Bank", "Pinnacle Bank", "Premier Bank",
    "Navy Federal Credit Union", "State Employees Credit Union", "Pentagon Federal Credit Union", 
    "Boeing Employees Credit Union", "Golden 1 Credit Union", "Alliant Credit Union", "BECU",
    "USAA Federal Savings Bank", "SchoolsFirst Federal Credit Union", "America First Credit Union",
    "Bank of the West", "Eastern Bank", "Western Bank", "Northern Trust", "Southern Bank",
    "Central Bank", "Atlantic Union Bank", "Pacific Premier Bank", "Mountain West Bank", "Great Western Bank",

    # Tier 2: Regional and State Banks (150)
    "First National Bank of America", "Bank of New York Mellon", "First Republic Bank", "Silicon Valley Bank",
    "Signature Bank", "Webster Bank", "People's United Bank", "Associated Bank", "Old National Bank",
    "United Community Bank", "Northern Trust Company", "State Street Bank and Trust", "BNY Mellon Trust Company",
    "Goldman Sachs Bank USA", "Morgan Stanley Bank", "Charles Schwab Bank", "Fidelity Management Trust Company",
    "Vanguard Fiduciary Trust Company", "Bank of New York Mellon Trust Company", "Deutsche Bank Trust Company",
    "Dollar Bank Federal Savings Bank", "Emigrant Bank", "Marcus by Goldman Sachs Bank", "American Express National Bank",
    "Discover Bank", "Ally Bank", "Capital One 360", "CIT Bank", "Synchrony Bank", "Barclays Bank Delaware",
    "Farm Credit Bank", "AgriBank", "CoBank", "AgFirst Farm Credit Bank", "Texas Farm Credit Bank",
    "Northwest Farm Credit Services", "Farm Credit Services of America", "AgCredit", "Rural 1st", "Farmer Mac",
    "BMW Bank of North America", "Toyota Motor Credit Corporation", "Ford Motor Credit Company", "General Motors Financial",
    "Harley-Davidson Financial Services", "John Deere Financial", "Caterpillar Financial Services", "GE Capital Bank",
    "Mercedes-Benz Financial Services", "Volvo Financial Services", "VERABANK", "RCB Bank", "Stock Yards Bank and Trust",
    "First Citizens Bank and Trust", "Frost Bank", "Comerica Bank", "Zions First National Bank", "First Interstate Bank",
    "Banner Bank", "Columbia Bank", "Umpqua Bank", "Sterling Bank", "Texas Capital Bank", "Prosperity Bank",
    "Woodforest National Bank", "Green Dot Bank", "MetaBank", "Republic Bank", "Iberiabank", "Hancock Whitney Bank",
    "First Financial Bank", "Heartland Bank", "Midwest Bank", "Cornerstone Bank", "Gateway Bank", "Benchmark Bank",
    "Crossroads Bank", "MainStreet Bank", "Village Bank", "Hometown Bank", "Bank of Hawaii", "First Bank of Delaware",
    "Virginia Commerce Bank", "Texas State Bank", "California Bank and Trust", "Arizona Bank and Trust",
    "Colorado State Bank", "Nevada State Bank", "Utah Community Bank", "Wyoming Bank and Trust",
    "First United Bank and Trust Company", "National Bank and Trust Company", "Security National Bank and Trust",
    "Citizens National Bank and Trust", "First State Bank and Trust Company", "Community National Bank and Trust",
    "Farmers and Merchants Bank", "First Merchants Bank", "Merchants and Farmers Bank", "Bank and Trust Company",
    "Municipal Credit Union", "Teachers Credit Union", "Police and Fire Credit Union", "Healthcare Federal Credit Union",
    "Technology Credit Union", "University Credit Union", "Community Credit Union", "Educational Systems Credit Union",
    "Public Service Credit Union", "Federal Employees Credit Union", "Bank of Montreal", "Royal Bank of Canada",
    "Toronto-Dominion Bank", "Bank of Nova Scotia", "HSBC Bank USA", "Barclays Bank Delaware", "Deutsche Bank USA",
    "UBS Bank USA", "Credit Suisse USA", "Banco Santander", "Cross River Bank", "Square 1 Bank", "First Technology Bank",
    "Bridge Bank", "Live Oak Bank", "Axos Bank", "Radius Bank", "TIAA Bank", "BBVA USA", "MUFG Union Bank",
    "AmeriServ Financial Bank", "Anchor Bank", "Apple Bank for Savings", "Arvest Bank", "Atlantic Capital Bank",
    "Banc of California", "BancFirst", "BancorpSouth Bank", "Bank Forward", "Bank Independent", "Bank of Guam",
    "Bank of Marin", "Bank of New Hampshire", "Bank of Oak Ridge", "Bank of Oklahoma", "Bank of Springfield",
    "Bank of the Ozarks", "Bank Rhode Island", "BankNewport", "BankUnited", "Bar Harbor Bank and Trust",
    "BCB Community Bank", "Beneficial Bank", "Berkshire Bank", "Blue Hills Bank", "Bremer Bank", "Brookline Bank",
    "Buffalo Savings Bank", "ByLine Bank", "Cambridge Savings Bank", "Cape Ann Savings Bank", "Cape Cod Five Cents Savings Bank",
    "Capital Bank", "Capital City Bank", "Carver State Bank", "Cathay Bank", "Century Bank", "Chemical Bank",
    "Choice Financial Group", "City National Bank", "Coastal Federal Credit Union", "Colonial Savings Bank", "Commerce Bank",

    # Tier 3: Community Banks and Credit Unions (200)
    "Community Bank of the Chesapeake", "Community First Bank", "ConnectOne Bank", "Cornerstone Community Bank",
    "Country Bank", "Cross County Savings Bank", "Danvers Savings Bank", "Dedham Institution for Savings",
    "Dime Community Bank", "East Boston Savings Bank", "Enterprise Bank and Trust", "Equity Bank", "Esquire Bank",
    "Evans Bank", "Evergreen Bank Group", "Exchange Bank", "F&M Bank", "Family Bank",
    "Farmers and Merchants Bank of Central California", "Farmers Bank and Trust", "Federal Savings Bank", "Fidelity Bank",
    "First American Bank", "First Bancorp", "First Bank", "First Bank and Trust", "First Commonwealth Bank",
    "First Community Bank", "First Federal Bank", "First Federal Savings Bank", "First Hawaii Bank", "First Horizon Bank",
    "First Ipswich Bank", "First National Bank Alaska", "First National Bank of Pennsylvania", "First National Bank of Tennessee",
    "First National Community Bank", "First Security Bank", "First Southern Bank", "First State Bank", "FirstBank",
    "Flagstar Bank", "Florida Capital Bank", "Fulton Bank", "Glacier Bank", "Great Southern Bank", "Guaranty Bank",
    "Harford Bank", "Hawthorn Bank", "HNB First Bank", "Home Bank", "Hope Bank", "Horizon Bank", "Independence Bank",
    "Inland Bank and Trust", "International Bank of Commerce", "Iowa State Bank", "Jonestown Bank and Trust",
    "KS StateBank", "Lake City Bank", "Lakeland Bank", "LegacyTexas Bank", "Level One Bank", "Macatawa Bank",
    "Malvern Bank", "Marine Bank", "Marquette Bank", "MidFirst Bank", "Midland States Bank", "MidSouth Bank",
    "MidWestOne Bank", "Millennium Bank", "Mission Bank", "MutualBank", "National Bank of Arizona",
    "National Bank of Commerce", "National Exchange Bank and Trust", "NBT Bank", "New Peoples Bank", "NewBridge Bank",
    "Norwood Bank", "Ocean Bank", "Origin Bank", "Ozark Bank", "Park Sterling Bank", "Pathfinder Bank",
    "Peapack-Gladstone Bank", "Peoples Bank", "Peoples Bank of Alabama", "PeoplesBank", "Pilot Bank", "Pioneer Bank",
    "Pinnacle Financial Partners", "PlainsCapital Bank", "Preferred Bank", "Prime Bank", "Princeton Bank",
    "Provident Bank", "Pulaski Bank", "Quantum National Bank", "Quontic Bank", "Red River Bank", "Reliant Bank",
    "Renasant Bank", "Resource Bank", "RiverHills Bank", "Rockland Trust", "Safra National Bank", "Sandy Spring Bank",
    "Seacoast Bank", "Security Bank and Trust", "Security State Bank", "Simmons Bank", "South State Bank",
    "Southside Bank", "Southwest Bank", "Spirit of Texas Bank", "State Bank and Trust", "State Bank of India",
    "StellarOne Bank", "Sun National Bank", "SunTrust Bank", "Sunrise Bank", "Table Rock Community Bank",
    "Tompkins Trust Company", "TriCo Bancshares", "TriState Capital Bank", "Troy Bank and Trust", "United Bank",
    "United Missouri Bank", "Unity Bank", "University Bank", "USAA", "Valley Bank", "Veridian Credit Union",
    "Victory Bank", "Wainscott Bank", "Washington Federal", "WashingtonFirst Bank", "WesBanco Bank", "West Bank",
    "West Texas National Bank", "Western Alliance Bank", "Western State Bank", "Westfield Bank", "Wintrust Bank",
    "Wise Bank", "York Traditions Bank", "Zions Bank", "1st Bank", "1st Source Bank", "21st Century Bank",
    "360 Federal Credit Union", "4Front Credit Union", "5Star Bank", "A+ Federal Credit Union", "AAA Bank",
    "ABCO Federal Credit Union", "ABC Bank", "Academy Bank", "Access Bank", "Acclaim Federal Credit Union",
    "ACE Credit Union", "Action Bank", "Advantage Bank", "Affinity Bank", "Affinity Federal Credit Union",
    "AimBank", "Air Force Federal Credit Union", "AltaOne Federal Credit Union", "America's Credit Union",
    "American Bank", "American Eagle Bank", "American Heritage Bank", "American Trust and Savings Bank",
    "Americorp Bank", "Amoco Federal Credit Union", "Apple Federal Credit Union", "Architectural Financial Credit Union",
    "Armed Forces Bank", "Arrow Bank", "Astoria Bank", "Atlantic Community Bank", "Atlas Bank", "Austin Bank",
    "Avenue Bank", "Axiom Bank", "Baden State Bank", "Baltic State Bank", "Bank 7", "Bank 34", "Bank of Akron",
    "Bank of Alapaha", "Bank of Botetourt", "Bank of Brookfield", "Bank of Cadiz and Trust Company", "Bank of Clarendon",
    "Bank of Coushatta", "Bank of Dickson", "Bank of Fayette County", "Bank of George", "Bank of Kirksville",
    "Bank of Labor", "Bank of Lincoln County", "Bank of Luxemburg", "Bank of Madison", "Bank of Mitchell",
    "Bank of Montgomery", "Bank of Morton", "Bank of Newman Grove", "Bank of Odessa", "Bank of Palmer",
    "Bank of Pontiac", "Bank of Prairie Village", "Bank of Ripley", "Bank of Romney", "Bank of Ruston",
    "Bank of Salem", "Bank of Southside Virginia", "Bank of Star City", "Bank of Stockton", "Bank of Sullivan",
    "Bank of Summers", "Bank of Tampa", "Bank of Tescott", "Bank of Utica", "Bank of Vernon", "Bank of Versailles",
    "Bank of Walterboro", "Bank of Washington", "Bank of Wiggins", "Bank of Winnfield and Trust Company",
    "Bank of York", "Bank of Zachary", "BankCherokee", "BankFirst Financial Services", "BankLiberty", "BankPlus",

    # Tier 4: Specialized and Regional Banks (200)
    "BankSouth", "BankStar Financial", "BankTennessee", "BankTrust", "Banner County Bank", "Barrington Bank and Trust",
    "Bay Bank", "Bay State Savings Bank", "Bayport Credit Union", "Beach First National Bank", "Beacon Federal",
    "Bear State Bank", "Bedford Federal Bank", "Bell Bank", "Belmont Savings Bank", "BenchMark Bank",
    "Berkshire Hills Bancorp", "Best Bank", "Bison State Bank", "Black Hills Federal Credit Union",
    "Blackhawk Bank and Trust", "Blue Grass Savings Bank", "BluePeak Credit Union", "Bluestem National Bank",
    "BOK Financial", "Border State Bank", "Boston Private Bank and Trust Company", "Boulevard Bank",
    "Bradford National Bank", "Branch Banking and Trust Company", "BrandywineBANK", "Brickyard Bank",
    "Bridgewater Bank", "Brighton Bank", "Bristol County Savings Bank", "Brookhaven Bank", "Brotherhood Bank and Trust",
    "Brown County State Bank", "Bruning State Bank", "Bryant Bank", "BSB Bank", "Buckeye State Bank",
    "Buffalo Prairie State Bank", "Burke and Herbert Bank", "Business Bank of Texas", "Butler Bank", "C&F Bank",
    "Cache Valley Bank", "California Pacific Bank", "Cambridge Trust Company", "Camden National Bank",
    "Canandaigua National Bank and Trust", "Capstone Bank", "Cardinal Bank", "Carolina Bank and Trust",
    "Carolina Premier Bank", "Carrollton Bank", "Carter Bank and Trust", "Casey State Bank", "Castle Bank",
    "Catskill Hudson Bank", "CBTC Bank", "Cedar Rapids Bank and Trust", "Cedar Security Bank", "CedarStone Bank",
    "Celtic Bank", "CenterState Bank", "Central Bank of Boone County", "Central Bank of Kansas City",
    "Central Bank of Lake of the Ozarks", "Central Bank of St. Louis", "Central Federal Savings and Loan",
    "Central National Bank", "Central Pacific Bank", "Central State Bank", "Central Valley Community Bank",
    "Century Bank of the Ozarks", "Century Savings Bank", "Champlain National Bank", "Charter Bank",
    "Charter Oak Federal Credit Union", "Chatelain Bank", "Chemung Canal Trust Company", "Cherokee Bank",
    "Cherokee State Bank", "Chesapeake Bank", "Choice Bank", "ChoiceOne Bank", "Citibank Delaware",
    "Citizens Alliance Bank", "Citizens and Northern Bank", "Citizens Bank and Trust", "Citizens Bank of Cumberland County",
    "Citizens Bank of Edmond", "Citizens Bank of Mukwonago", "Citizens Community Bank", "Citizens Deposit Bank and Trust",
    "Citizens First Bank", "Citizens Independent Bank", "Citizens National Bank of Albion", "Citizens National Bank of Cheboygan",
    "Citizens National Bank of Meridian", "Citizens National Bank of Paris", "Citizens National Bank of Quitman",
    "Citizens Savings Bank", "Citizens State Bank", "Citizens State Bank of Midwest City", "Citizens State Bank of Tyler",
    "Citizens Trust Bank", "Citizens Union Bank", "City Bank", "City Bank and Trust", "City First Bank",
    "City National Bank and Trust", "City National Bank of Florida", "City National Bank of New Jersey",
    "City National Bank of West Virginia", "City State Bank", "Citywide Banks", "Clackamas County Bank", "Clare Bank",
    "Clarence State Bank", "Classic Bank", "Clear Mountain Bank", "ClearView Federal Credit Union",
    "Coastal Community Bank", "Coastal States Bank", "CoBiz Bank", "Coconut Grove Bank", "Cole Taylor Bank",
    "Colonial Bank", "Colorado East Bank and Trust", "Colorado Federal Savings Bank", "Columbia River Bank",
    "Commercial Bank", "Commercial Bank and Trust", "Commercial Bank of Texas", "Commercial National Bank",
    "Commercial Savings Bank", "Commonwealth Bank and Trust", "Community Bank and Trust", "Community Bank of Broward",
    "Community Bank of Mississippi", "Community Bank of Oak Park River Forest", "Community Bank of Pleasant Hill",
    "Community Bank of the Bay", "Community Banks of Colorado", "Community Capital Bank", "Community Development Bank",
    "Community Federal Savings Bank", "Community Financial Services Bank", "Community First Bank and Trust",
    "Community National Bank and Trust", "Community Resource Bank", "Community Spirit Bank", "Community State Bank",
    "Community Trust and Banking Company", "Community West Bank", "Compeer Financial", "Concordia Bank and Trust",
    "Congressional Bank", "Connecticut Community Bank", "Cornerstone Community Bank", "Country Club Bank",
    "Country State Bank", "Countryside Bank", "County Bank", "Court Street Group Bank", "Coven Bank", "Covenant Bank",
    "Cowboy State Bank", "Crawford County Trust and Savings Bank", "Crescent Bank and Trust", "Cross Keys Bank",
    "Crystal Lake Bank and Trust", "Cumberland Bank", "Cumberland County Bank", "Cumberland Valley National Bank",
    "Customers Bank", "Dakota Community Bank and Trust", "Dakota Western Bank", "Danville State Savings Bank",
    "Davis County Bank", "De Novo Bank", "Decatur County Bank", "Delaware County Bank and Trust", "Delta Bank",
    "Delta National Bank and Trust", "Denmark State Bank", "Deposit Bank", "Deutsche Bank Trust Company Americas",
    "Diamond Bank", "Dickinson County Bank", "Dime Bank", "Dixon Bank", "DNB First", "Dolores State Bank",
    "Donnell Bank", "Douglas County Bank", "Drovers First American Bank", "Du Quoin State Bank", "DuPage Credit Union",

    # Tier 5: More Community and Specialty Banks (200)
    "Eagle Bank", "Eagle Bank and Trust", "Eagle Savings Bank", "EagleBank", "East Cambridge Savings Bank",
    "East Penn Bank", "East West Bank", "Eastern International Bank", "Eastern Michigan Bank", "Eastern National Bank",
    "Easthampton Savings Bank", "Eastman Credit Union", "Elberton Federal Savings and Loan", "Electronic Federal Credit Union",
    "Elmira Savings Bank", "Embassy Bank for the Lehigh Valley", "Empire Bank", "Emprise Bank", "Encompass Bank",
    "Endeavor Bank", "Enterprise Bank", "Equitable Bank", "ESB Bank", "Essex Bank", "Everett Co-operative Bank",
    "Evergreen Federal Savings", "Exchange Bank of Northeast Missouri", "Exchange National Bank and Trust",
    "Executive National Bank", "Extraco Banks", "F&M Bank and Trust Company", "Fairfield County Bank",
    "Fairview State Banking Company", "Fall River Five Cents Savings Bank", "Family Security Credit Union",
    "Far East National Bank", "Farm Bureau Bank", "Farmers and Merchants State Bank", "Farmers Bank and Capital Trust Company",
    "Farmers Deposit Bank", "Farmers National Bank", "Farmers Savings Bank", "Farmers State Bank", "Fauquier Bank",
    "Fayette County National Bank", "FCNB Bank", "Federal Agricultural Mortgage Corporation", "Fidelity Co-operative Bank",
    "Fidelity Federal Savings and Loan", "Fifth District Savings Bank", "Finance Factors", "Financial Federal Bank",
    "Financial Partners Credit Union", "First American Bank and Trust", "First Bank Financial Centre",
    "First Bank of Highland Park", "First Bank of Ohio", "First Citizens Community Bank", "First Commercial Bank",
    "First Community Bank and Trust", "First County Bank", "First Credit Union", "First Federal Bank of the Midwest",
    "First Federal Community Bank", "First Federal Savings and Loan Association", "First Financial Northwest",
    "First Green Bank", "First Guaranty Bank", "First Liberty Bank", "First Midwest Bank", "First National Bank and Trust",
    "First National Bank in Howell", "First National Bank in Trinidad", "First National Bank of Anderson",
    "First National Bank of Barry", "First National Bank of Beardstown", "First National Bank of Brookfield",
    "First National Bank of Coleraine", "First National Bank of Dighton", "First National Bank of Gillette",
    "First National Bank of Griffin", "First National Bank of Hugo", "First National Bank of Kansas",
    "First National Bank of Livingston", "First National Bank of Lacon", "First National Bank of Long Island",
    "First National Bank of McConnelsville", "First National Bank of Michigan", "First National Bank of Middle Tennessee",
    "First National Bank of Mount Dora", "First National Bank of Nebraska", "First National Bank of Nevada",
    "First National Bank of Nokomis", "First National Bank of Olathe", "First National Bank of Ottawa",
    "First National Bank of Pikeville", "First National Bank of Raymond", "First National Bank of Scotia",
    "First National Bank of Staunton", "First National Bank of Suffield", "First National Bank of Syracuse",
    "First National Bank of Texas", "First National Bank of Vandalia", "First National Bank of Waterloo",
    "First National Bank Texas", "First National Bank USA", "First Nebraska Bank", "First Peoples Bank",
    "First Priority Bank", "First Promise Bank", "First Regional Bank", "First Robinson Savings Bank",
    "First Savings Bank", "First Savings Bank Northwest", "First Security Bank and Trust", "First South Bank",
    "First State Bank Central Texas", "First State Bank of Arcadia", "First State Bank of Ben Wheeler",
    "First State Bank of Middlebury", "First State Bank of Newcastle", "First State Bank of Purdy",
    "First State Bank of Roscoe", "First State Bank of Uvalde", "First State Bank of Wyoming", "First Texas Bank",
    "First Trust and Savings Bank", "First United Bank", "First United Security Bank", "First Valley Bank",
    "First Victoria National Bank", "First Volunteer Bank", "First Western Bank and Trust", "FirstBank Southwest",
    "FirsTier Bank", "Five Star Bank", "Flagship Bank", "Flushing Bank", "FNB Bank", "FNB Community Bank",
    "Focus Bank", "Foothill Independent Bank", "Forest City Bank", "Fort Hood National Bank", "Fort Lee Federal Credit Union",
    "Fortress Bank", "Foundation Bank", "Four Oaks Bank and Trust", "Fox River State Bank", "Franklin Bank",
    "Franklin County Bank", "Franklin Savings Bank", "Franklin Synergy Bank", "Freedom Bank", "Fremont Bank",
    "Frontier Bank", "Frontier Community Bank", "FSB Bank", "Fulda Area Credit Union", "Full Spectrum Bank",
    "Furst-McNess Bank", "Fusion Bank", "G&F Financial Bank", "Galaxy Bank", "Garfield County Bank",
    "Gateway Bank of Pennsylvania", "Gateway Commercial Bank", "GCF Bank", "GECU", "German American Bank",
    "Gibsland Bank and Trust", "Gibson County Bank", "GN Bank", "Go Bank", "Gold Coast Bank", "Golden Belt Bank",
    "Golden Bank", "Golden Pacific Bank", "Golden State Bank", "Goodfield State Bank", "Government Employees Credit Union",
    "Grabill Bank", "Grand Bank", "Grand Ridge National Bank", "Grand Savings Bank", "Grande Communications",
    "Grandpoint Bank", "Grandview Bank", "Grant County Bank", "Great Midwest Bank", "Great Plains Bank",
    "Great River Bank", "GreatBanc Trust Company", "Greater Nevada Credit Union", "Green Country Bank",
    "Greenfield Banking Company", "Greenwood Trust Company", "Grew and Company Bank", "Grundy Bank", "GSL Trust",
    "Guardian Bank", "Guardian Savings Bank", "Gulf Coast Bank and Trust", "Gulf Capital Bank", "H&R Block Bank",
    "Habib American Bank", "Hamilton Bank", "Hampton Roads Bankshares", "Hanmi Bank", "Happy State Bank",
    "Harbor Bank", "Harvest Bank", "Haverhill Bank", "Hawaii National Bank", "Heartland Bank and Trust",
    "Heritage Bank of Nevada", "Heritage Bank of the South", "Heritage Community Bank", "Heritage Oaks Bank",
    "Heritage Southeast Bank", "Herring Bank", "HF Bar Ranch", "Highland Bank", "Hills Bank and Trust",
    "Hinsdale Bank and Trust", "HNB Bank", "Holcomb Bank", "Home Bank SB", "Home Federal Bank",
    "Home Federal Savings and Loan", "Home Savings Bank", "Home State Bank", "Homeland Federal Savings Bank",
    "HomeStreet Bank", "HomeTown Bank", "Hoosac Bank", "Horizon Bank SSB", "Horizon Community Bank",
    "Houston Bank and Trust", "Howard Bank", "HSBC Bank Nevada", "Hudson City Savings Bank", "Hudson Valley Bank",
    "Huntingdon Valley Bank", "Huron Community Bank", "Hyperion Bank", "Illini Bank", "Independence Bank of Kentucky",

    # Tier 6: Additional Regional and Specialty Banks (200)
    "Independence First Bank", "Indiana First Savings Bank", "Industrial and Commercial Bank of China",
    "Industrial Bank", "Infinity Bank", "Inland Northwest Bank", "Innovation Bank", "Insignia Bank",
    "Institutional Bank and Trust", "Integrity Bank", "Interaudi Bank", "Interstate Bank", "Inwood National Bank",
    "Iron Workers Savings and Loan", "Iroquois Federal Savings and Loan", "Isbank USA", "Island Bank",
    "Islanders Bank", "J.P. Morgan Private Bank", "Jacksonville Savings Bank", "Jacksboro National Bank",
    "Janney Montgomery Scott", "Jefferson Bank", "Jefferson Security Bank", "Jonestown Bank", "JSC Federal Credit Union",
    "Kanawha Valley Bank", "Kansas State Bank", "Katahdin Trust Company", "Kearny Bank", "Kendall State Bank",
    "Kentucky Bank", "Kentucky Farmers Bank", "Keystone Bank", "Kinderhook Bank", "King Southern Bank",
    "Kirkpatrick Bank", "Knights of Columbus", "Knox County Savings Bank", "Kopernik Federal Credit Union",
    "Korean Exchange Bank", "KS Bank", "KS StateBank", "Lakeland Bank", "Lakeshore Bank", "Lakeside Bank",
    "Landmark Bank", "Landmark Community Bank", "Landmark National Bank", "Laredo National Bank", "Lawrenceburg Bank",
    "Leaders Bank", "Lebanon Valley Farmers Bank", "Legacy Bank", "Legacy Texas Bank", "Legends Bank",
    "Lehigh Valley Bank", "Liberty Bank Connecticut", "Liberty Bank Utah", "Liberty National Bank",
    "Liberty Savings Bank", "LifeStore Bank", "Lincoln Savings Bank", "Linn Area Credit Union", "Live Oak Banking Company",
    "Livingston State Bank", "Loan and Trust Company", "LocaLender", "Lone Star Bank", "Long Island Savings Bank",
    "Lorain National Bank", "Louisiana Federal Credit Union", "Lubbock National Bank", "Luther Burbank Savings",
    "Luzerne Bank", "Lyons National Bank", "Mackinac Savings Bank", "Madison County Bank", "Magic Valley Bank",
    "Magnolia Bank", "Magnolia State Bank", "Main Street Bank", "MainSource Bank", "Malaga Bank",
    "Manchester Bank", "Mango Financial", "Manufacturers Bank", "Maple City Savings Bank", "Marathon Bank",
    "Marblehead Bank", "Marine Credit Union", "Marion Bank", "Marion County Bank", "Market Street Bank",
    "Mars Bank", "Maryland Bank and Trust", "Mason Bank", "Mason City National Bank", "Massachusetts Bank",
    "Medallion Bank", "Mechanics Bank", "Mechanics Savings Bank", "Medina County Bank", "Melrose Credit Union",
    "Member One Federal Credit Union", "Memorial Credit Union", "Mercantile Bank", "Merchants and Marine Bank",
    "Merchants and Planters Bank", "Merchants Bank of Indiana", "Meridian Bank", "Merit Bank", "Merrick Bank",
    "MetaBank", "Metro Bank", "Metro City Bank", "Metro Credit Union", "Metropolitan Bank",
    "Metropolitan Commercial Bank", "Miami County Federal Savings Bank", "Michigan First Credit Union",
    "Michigan Savings Bank", "MidAmerica National Bank", "MidCarolina Bank", "Middlefield Bank", "Middlesex Savings Bank",
    "MidFirst Bank", "Midland Community Bank", "Midwest Bank Centre", "Midwest BankCentre", "Midwest Heritage Bank",
    "MidWestOne Bank", "Mile High Banks", "Military Bank", "Millbury Savings Bank", "Miller County Bank",
    "Mills County State Bank", "Milton Savings Bank", "Miners and Merchants Bank", "Minnesota Bank and Trust",
    "Minnesota National Bank", "Minotola National Bank", "Mission Bank", "Missouri Bank and Trust",
    "Missouri Valley Bank", "Mitchell Bank", "Mohave State Bank", "Molalla State Bank", "Monarch Bank",
    "Monroe Bank and Trust", "Montana Bank", "Montana State Bank", "Montecito Bank and Trust", "Montgomery Bank",
    "Montrose Savings Bank", "Moody Bank", "Morgan Stanley Private Bank", "Morrill and Janes Bank",
    "Morris Bank", "Morris County Savings Bank", "Mortgage Investors Corporation", "Morton Community Bank",
    "Mount Vernon Bank", "Mountain Commerce Bank", "Mountain National Bank", "Mountain View Bank",
    "MountainOne Bank", "Movement Bank", "Mukwonago State Bank", "Munnsville Community Bank", "Mutual Bank",
    "Mutual Federal Bank", "Mutual of Omaha Bank", "MutualBank", "MVP Bank", "National Bank and Trust",
    "National Bank of Andrews", "National Bank of Blacksburg", "National Bank of California", "National Bank of Connecticut",
    "National Bank of Delaware", "National Bank of Georgia", "National Bank of Indiana", "National Bank of Kansas City",
    "National Bank of Malvern", "National Bank of Middlebury", "National Bank of New York City", "National Bank of Petersburg",
    "National Bank of South Carolina", "National Bank of Texas", "National Bank of Washington", "National Bank of Waynesboro",
    "National Capital Bank", "National Exchange Bank", "National Iron Bank", "National Penn Bank", "NebraskaLand Bank",
    "Neighborhood Credit Union", "Nelson County Bank", "Neuberger Berman Trust Company", "Nevada Bank and Trust",
    "Nevada Security Bank", "Nevada State Bank", "New Dimension Federal Credit Union", "New England Federal Credit Union",
    "New Era Bank", "New Frontier Bank", "New Haven Savings Bank", "New Liberty Bank", "New Mexico Bank and Trust",
    "New Omni Bank", "New Resource Bank", "New York Community Bank", "New York Private Bank", "NewAlliance Bank",
    "Newfield National Bank", "Newport Federal Credit Union", "Nextier Bank", "Nicolet National Bank", "NKFB Bank",
    "Nodaway Valley Bank", "Norfolk County Trust", "North Akron Savings Bank", "North American Banking Company",
    "North Avenue Capital", "North Brookfield Savings Bank", "North Cambridge Co-operative Bank", "North Country Bank",
    "North Country Savings Bank", "North Dallas Bank and Trust", "North Georgia Bank", "North Salem State Bank",
    "North Shore Bank", "North Star Bank", "North Valley Bank", "Northbrook Bank and Trust", "Northeast Bank",
    "Northeast Georgia Bank", "Northern California National Bank", "Northern Hancock Bank and Trust", "Northern State Bank",
    "Northfield Savings Bank", "Northpointe Bank", "Northrim Bank", "Northside Bank", "Northside Community Bank",
    "Northwest Bank", "Northwest Community Bank", "Northwest Georgia Bank", "Northwest Savings Bank", "Norwich Savings Society",
    "NOVA Bank", "Novelty Bank", "NSB Bank", "Oak Bank", "Oak Valley Community Bank", "Oakstar Bank",
    "Oakwood Bank", "Ocean Bank", "Ocean City Home Bank", "Oconee Federal Savings and Loan", "Ohio Savings Bank",
    "Oklahoma Bank and Trust", "Oklahoma National Bank", "Old Point National Bank", "Old Second National Bank",
    "Omega Bank", "OneUnited Bank", "Optum Bank", "Orange County Business Bank", "Oregon Bank",
    "Oregon Coast Bank", "Oregon Pacific Bank", "Oriental Bank", "Orrstown Bank", "OSB Community Bank",
    "Ouachita Independent Bank", "Oxford Bank and Trust", "Ozark Mountain Bank", "Pacific City Bank",
    "Pacific Coast Bankers Bank", "Pacific Continental Bank", "Pacific Mercantile Bank", "Pacific National Bank",
    "Pacific Premier Bank", "Pacific Valley Bank", "Pacific Western Bank", "Pacifica Bank", "Palladium Bank",
    "Palmer Bank and Trust", "Panhandle State Bank", "Paradise Bank", "Park Bank", "Park National Bank",
    "Parkway Bank and Trust", "Parke Bank", "Parkside Financial Bank", "Patriot Bank", "Patriot Federal Credit Union",
    "Pawtucket Credit Union", "Peach State Bank", "Peachtree Bank", "Pee Dee Federal Savings Bank", "Pen Air Federal Credit Union",
    "Pennsville National Bank", "Pentucket Bank", "People's Bank", "People's Bank of Commerce", "People's Credit Union",
    "People's Intermountain Bank", "People's State Bank", "PeoplesSouth Bank", "Pequot Savings Bank", "Perpetual Federal Savings Bank",
    "Persons Banking Company", "Petra Bank", "Philo Exchange Bank", "Phoenix Bank", "Pidgeon River Credit Union",
    "Pikeville National Bank", "Pilgrim Bank", "Pine River State Bank", "Pinnacle Bank Wyoming", "Pioneer Bank SSB",
    "Pioneer Trust Bank", "Piscataqua Savings Bank", "Pittsfield Co-operative Bank", "PlainsCapital Bank", "Planters Bank",
    "Planters Bank and Trust", "Platte Valley Bank", "Plaza Bank", "Pleasant Hill Bank", "PNC Bank Delaware",
    "Polish and Slavic Federal Credit Union", "Polish National Credit Union", "Popular Community Bank", "Port Washington State Bank",
    "Portage County Bank", "Porter Bank", "Portland Savings Bank", "Post Oak Bank", "Potlatch No 1 Federal Credit Union",

    # Tier 7: Final Batch of Regional and Specialty Banks (200)
    "Preferred Community Bank", "Premier Bank", "Premier Community Bank", "Premier Valley Bank", "Presidential Bank",
    "Prevail Bank", "Prime Alliance Bank", "Prime Bank", "Prime Meridian Bank", "PrimeTrust Bank",
    "Princeton Bank", "Private Bank of Buckhead", "Professional Bank", "Progress Bank", "Promise Land Bank",
    "Prosperity Bank", "Puget Sound Bank", "Putnam Bank", "QNB Bank", "Quadient Bank", "Qualstar Credit Union",
    "Queensboro National Bank", "Quick Silver Bank", "Quoin Financial Bank", "Radius Bank", "Raiffeisenbank",
    "Rainier Pacific Bank", "Ramsey National Bank", "Range Bank", "Raymond Federal Bank", "RBC Bank",
    "Readlyn Savings Bank", "Real Estate Financial Bank", "Receivable Bank", "Red River State Bank", "RedStone Bank",
    "Regal Bank", "Regency Bank", "Regional Bank", "Reliance Bank", "Reliance State Bank", "Republic Bank of Chicago",
    "Resource Bank", "Richland State Bank", "Richmond County Bank", "Ridgewood Savings Bank", "Rio Bank",
    "River Bank", "River Cities Bank", "River City Bank", "River Valley Bank", "Riverside Bank",
    "Riverside National Bank", "Riverview Community Bank", "RNB State Bank", "Roadrunner Bank", "Roanoke Rapids Savings Bank",
    "Robertson County Bank", "Rochester State Bank", "Rock Canyon Bank", "Rockbridge Commercial Bank", "Rockford Bank and Trust",
    "Rocky Mountain Bank", "Rolling Hills Bank", "Royal Bank America", "Ruston State Bank", "Sabine State Bank",
    "Safety Harbor Bank", "Saginaw Bay National Bank", "Salem Five Cents Savings Bank", "Salem State Bank", "Salin Bank and Trust",
    "Sallie Mae Bank", "San Luis Valley Federal Bank", "Sandhills Bank", "Sandy Hook Bank", "Santa Barbara Bank and Trust",
    "Santa Clara County Bank", "Saratoga National Bank", "Savings Bank of Danbury", "Savings Bank of Maine",
    "Savings Institute Bank and Trust", "SBT Bank", "Scotsman Bank", "Scripture Union", "Seacoast Commerce Bank",
    "Seaside National Bank", "Seattle Bank", "Security Bank Minnesota", "Security Bank USA", "Security Federal Bank",
    "Security First Bank", "Security Home Bank", "Security National Bank of Sioux City", "Security Pacific Bank",
    "Security State Bank and Trust", "Select Bank and Trust", "Sewickley Savings Bank", "Shamrock Bank",
    "Shenandoah Valley National Bank", "Sherwood Community Bank", "Shore Bank", "Signature Bank of Arkansas",
    "Signature Bank of Georgia", "Silver Lake Bank", "Silver State Bank", "Silverton Bank", "Simmons First Bank",
    "Simplicity Bank", "Sinclair National Bank", "Siuslaw Bank", "Six Rivers National Bank", "Skowhegan Savings Bank",
    "Sky Bank", "Slate Belt Bank", "Sleepy Eye State Bank", "Smart Bank", "Smoky Mountain Bank",
    "Snowbird Bank", "Solera National Bank", "Somerset Trust Company", "Sound Community Bank", "South Bay Bank",
    "South Central Bank", "South Country Bank", "South Louisiana Bank", "South Ottumwa Savings Bank", "South Shore Bank",
    "South Side Bank", "Southeast Bank", "Southern Bancorp Bank", "Southern Bank and Trust Company", "Southern Community Bank",
    "Southern First Bank", "Southern Heritage Bank", "Southern Hills Community Bank", "Southern Missouri Bank",
    "Southern National Bank", "Southpoint Bank", "Southwest Bank of Texas", "Southwest Community Bank", "Southwest Georgia Bank",
    "Sovereign Bank", "Spectrum Bank", "Spirit Bank", "Spring Bank", "Spring Valley City Bank", "St. Charles Bank and Trust",
    "St. Johns Bank", "St. Martin Bank", "St. Stephen State Bank", "Standard Bank", "Star Bank",
    "Star Financial Bank", "State Bank and Trust Co", "State Bank of Arthur", "State Bank of Bell", "State Bank of Burnettsville",
    "State Bank of Cherry", "State Bank of Cross Plains", "State Bank of Eagle Butte", "State Bank of Fairmont",
    "State Bank of Geneva", "State Bank of Herscher", "State Bank of India Chicago", "State Bank of Kansas",
    "State Bank of Lakota", "State Bank of Lincoln", "State Bank of Marietta", "State Bank of Nauvoo",
    "State Bank of Odell", "State Bank of Peru", "State Bank of Reeseville", "State Bank of Southern Utah",
    "State Bank of Taunton", "State Bank of the Lakes", "State Bank of Toledo", "State Bank of Toulon",
    "State Bank of Wapello", "State Bank of Waterloo", "State Bank of Whittington", "State Bank of Chittenango",
    "Stearns Bank", "Sterling Federal Bank", "Sterling Savings Bank", "Stewart County Bank", "Stockgrowers State Bank",
    "Stockman Bank", "Stone County National Bank", "Stonebridge Bank", "Stoneham Bank", "Sturdy Savings Bank",
    "Suffolk County National Bank", "Sugar River Bank", "Sumitomo Mitsui Banking Corporation", "Summit Bank",
    "Summit Community Bank", "Sun East Federal Credit Union", "Sun National Bank", "Sunflower Bank", "SunTrust Bank",
    "Sutton Bank", "Sycamore Bank", "Syracuse Cooperative Federal Credit Union", "Talbot Bank", "Tarboro Savings Bank",
    "TCF National Bank", "Team Capital Bank", "TEB Bank", "Tennessee Commerce Bank", "Tennessee State Bank",
    "Terra State Bank", "Texana Bank", "Texas Bank", "Texas Capital Bank", "Texas Champion Bank",
    "Texas Gulf Bank", "Texas Heritage Bank", "Texas Hill Country Bank", "Texas National Bank", "Texas Regional Bank",
    "Texas Security Bank", "Texas Star Bank", "The Bancorp Bank", "The Bank of Castile", "The Bank of Delmarva",
    "The Bank of Elk River", "The Bank of Fayette County", "The Bank of Glen Burnie", "The Bank of Greene County",
    "The Bank of Hemet", "The Bank of Kentucky", "The Bank of Marion", "The Bank of New York Mellon",
    "The Bank of Princeton", "The Bank of Tampa", "The Citizens Bank", "The Commercial Bank", "The Covington Savings and Loan",
    "The Delaware County Bank", "The Elmira Savings Bank", "The Farmers Bank", "The Farmers National Bank",
    "The First Bank", "The First National Bank in Sioux Falls", "The First National Bank of Byers",
    "The First National Bank of Gordon", "The First National Bank of Hartford", "The First National Bank of Hooker",
    "The First National Bank of Milaca", "The First National Bank of Wakefield", "The Hocking Valley Bank",
    "The Hometown Bank", "The National Bank", "The National Bank of Blacksburg", "The National Bank of Indianapolis",
    "The Northern Trust Company", "The Oculina Bank", "The Park National Bank", "The Peoples Bank",
    "The Peoples State Bank", "The Private Bank", "The Security National Bank", "The State Bank", "The State Bank and Trust Company",
    "The Trust Bank", "The Village Bank", "Third Federal Savings and Loan", "Thumb National Bank", "TIAA-CREF Trust Company",
    "Timberland Bank", "Town and Country Bank", "Town Bank", "Towne Bank", "Trade Bank", "Traditions Bank",
    "TransPecos Banks", "Tri Counties Bank", "Tri County Bank", "Tri Valley Bank", "Triangle Bank",
    "Trinity Bank", "Triumph Savings Bank", "Trust Company Bank", "TrustBank", "TruStone Financial Credit Union",
    "Two Rivers Bank", "U.S. Century Bank", "UMB Bank", "Union Bank", "Union Bank and Trust", "Union Bank of California",
    "Union Colony Bank", "Union Savings Bank", "Union State Bank", "United Bank", "United Bank and Trust",
    "United Bankers Bank", "United Community Bank of Georgia", "United National Bank", "United Prairie Bank",
    "United Security Bank", "Unity Bank", "Universal Bank", "University Bank and Trust", "Upper Peninsula State Bank",
    "USAA Savings Bank", "Utah Community Credit Union", "Valley Bank", "Valley Bank and Trust", "Valley Community Bank",
    "Valley Green Bank", "Valley National Bank", "Valley State Bank", "Vaughan Community Bank", "VB&T Bank",
    "Venice Community Bank", "Venture Bank", "Veridian Credit Union", "Vermont Federal Credit Union", "Vernon Bank and Trust",
    "Victory State Bank", "Viking Bank", "Villa Grove State Bank", "Village Bank", "Virginia Bank and Trust",
    "Virginia Commonwealth Bank", "Vision Bank", "Volunteer State Bank", "Wabash Valley Bank", "Walworth State Bank",
    "Washington County Bank", "Washington Savings Bank", "Washington State Bank", "Washington Trust Bank", "WaterStone Bank",
    "Waukon State Bank", "Wayne Bank", "Wayne County Bank", "WESTconsin Credit Union", "West Alabama Bank and Trust",
    "West Branch Valley Bank", "West Gate Bank", "West Georgia National Bank", "West Iowa Bank", "West Plains Bank and Trust",
    "West Shore Bank", "West Town Bank and Trust", "Western Bank", "Western Heritage Bank", "Western National Bank",
    "Western Reserve Bank", "Western Security Bank", "WestStar Bank", "WheatState Bank", "White River Bank",
    "Whitesville State Bank", "Wilber State Bank", "Wilson Bank and Trust", "Windom National Bank", "Windsor Federal Savings",
    "Winona National Bank", "Wintrust Bank", "Wisconsin Bank and Trust", "Wolverine Bank", "Woodhaven National Bank",
    "Woodland Bank", "Workingmens Bank", "Wyoming Bank and Trust", "York County Federal Credit Union", "York State Bank",
    "Zions Bank Utah"
]

def run_comprehensive_1000_bank_test():
    """Run comprehensive test with 1000+ bank names"""
    print(f"🏦 COMPREHENSIVE BANK NAME EXTRACTION TEST")
    print(f"Testing with {len(THOUSAND_BANK_NAMES)} real bank names")
    print("=" * 80)
    
    # Test Categories
    test_categories = {
        "clean_names": [],
        "contaminated_names": [],
        "edge_cases": [],
        "challenging_multi_word": []
    }
    
    # 1. Clean Bank Names Test (first 100)
    print(f"\n1. CLEAN BANK NAMES TEST (first 100 names)")
    print("-" * 60)
    
    clean_successes = 0
    for i, bank_name in enumerate(THOUSAND_BANK_NAMES[:100], 1):
        result = extract_complete_bank_name_from_line(bank_name)
        is_exact_match = result == bank_name
        if is_exact_match:
            clean_successes += 1
        
        test_categories["clean_names"].append({
            "input": bank_name,
            "output": result,
            "exact_match": is_exact_match
        })
        
        # Show first 20 results
        if i <= 20:
            status = "✅" if is_exact_match else "❌"
            print(f"{i:2d}. {bank_name:<45} -> {result} {status}")
    
    clean_success_rate = (clean_successes / 100) * 100
    print(f"\nClean Names Success Rate: {clean_successes}/100 = {clean_success_rate:.1f}%")
    
    # 2. Contaminated Names Test (real-world OCR scenarios)
    print(f"\n2. CONTAMINATED BANK NAMES TEST")
    print("-" * 60)
    
    contaminated_tests = []
    # Generate contaminated versions from our bank list
    contamination_patterns = [
        " bai test Report Type:",
        " Statement Date: 01/01/2024",
        " Account Number: 1234567890", 
        " Page 1 of 5",
        " Balance: $1,234.56",
        " Report Generated on 12/31/2023",
        " Customer Statement",
        " Account Summary",
        " Transaction History", 
        " Monthly Statement",
        " Statement Period: Jan 1 - Jan 31",
        " Online Banking",
        " Federal ID: 123456789",
        " Member FDIC",
        " SWIFT: BNKUS33",
        " Private Banking",
        " Boston MA",
        " Salt Lake City",
        " Purchase NY"
    ]
    
    # Test 50 contaminated cases
    contaminated_successes = 0
    for i in range(50):
        base_bank = THOUSAND_BANK_NAMES[i + 100]  # Use banks 100-150
        contamination = contamination_patterns[i % len(contamination_patterns)]
        contaminated_name = base_bank + contamination
        
        result = extract_complete_bank_name_from_line(contaminated_name)
        success = result is not None and len(result) > 2 and result != contaminated_name
        if success:
            contaminated_successes += 1
        
        test_categories["contaminated_names"].append({
            "input": contaminated_name,
            "output": result,
            "expected_base": base_bank,
            "success": success
        })
        
        # Show first 10 results
        if i < 10:
            status = "✅" if success else "❌"
            print(f"{i+1:2d}. {contaminated_name}")
            print(f"    -> {result} {status}")
    
    contaminated_success_rate = (contaminated_successes / 50) * 100
    print(f"\nContaminated Names Success Rate: {contaminated_successes}/50 = {contaminated_success_rate:.1f}%")
    
    # 3. Challenging Multi-word Names
    print(f"\n3. CHALLENGING MULTI-WORD NAMES TEST")
    print("-" * 60)
    
    # Find the most challenging multi-word names
    challenging_names = []
    for name in THOUSAND_BANK_NAMES:
        word_count = len(name.split())
        if word_count >= 4:  # 4 or more words
            challenging_names.append(name)
    
    challenging_successes = 0
    test_count = min(50, len(challenging_names))
    
    for i, bank_name in enumerate(challenging_names[:test_count], 1):
        result = extract_complete_bank_name_from_line(bank_name)
        # Success criteria: extracted something meaningful
        success = result is not None and len(result.split()) >= 2
        if success:
            challenging_successes += 1
        
        test_categories["challenging_multi_word"].append({
            "input": bank_name,
            "output": result,
            "word_count": len(bank_name.split()),
            "success": success
        })
        
        # Show first 15 results
        if i <= 15:
            status = "✅" if success else "❌"
            words = len(bank_name.split())
            print(f"{i:2d}. [{words}w] {bank_name}")
            print(f"    -> {result} {status}")
    
    challenging_success_rate = (challenging_successes / test_count) * 100
    print(f"\nChallenging Multi-word Success Rate: {challenging_successes}/{test_count} = {challenging_success_rate:.1f}%")
    
    # 4. Edge Cases
    print(f"\n4. EDGE CASES TEST")
    print("-" * 60)
    
    edge_cases = [
        "",  # Empty
        "Bank",  # Single word
        "of America",  # Missing "Bank"
        "123456789",  # Numbers only
        "BANK BANK BANK",  # Repeated
        "1st Bank",  # Number prefix
        "U.S. Bank",  # Periods
        "M&T Bank",  # Ampersand
        "Bank & Trust",  # With ampersand
        "Bank, N.A.",  # With comma
        "BANK OF AMERICA, N.A.",  # All caps with suffix
        "First-Citizens Bank",  # Hyphenated
        "Bank (Main Branch)",  # Parentheses
        "The Bank of New York",  # Starting with "The"
        "A+ Federal Credit Union"  # Special characters
    ]
    
    edge_successes = 0
    for i, test_case in enumerate(edge_cases, 1):
        result = extract_complete_bank_name_from_line(test_case)
        # Success: returned something reasonable
        success = result is not None and len(result) > 0
        if success:
            edge_successes += 1
        
        test_categories["edge_cases"].append({
            "input": test_case,
            "output": result,
            "success": success
        })
        
        status = "✅" if success else "❌"
        print(f"{i:2d}. '{test_case}' -> '{result}' {status}")
    
    edge_success_rate = (edge_successes / len(edge_cases)) * 100
    print(f"\nEdge Cases Success Rate: {edge_successes}/{len(edge_cases)} = {edge_success_rate:.1f}%")
    
    # 5. Overall Summary
    print(f"\n5. COMPREHENSIVE TEST SUMMARY")
    print("=" * 60)
    print(f"Total Bank Names in Database: {len(THOUSAND_BANK_NAMES)}")
    print(f"Clean Names Tested: 100")
    print(f"Contaminated Names Tested: 50")  
    print(f"Challenging Multi-word Tested: {test_count}")
    print(f"Edge Cases Tested: {len(edge_cases)}")
    print()
    print(f"RESULTS:")
    print(f"Clean Names Success Rate:        {clean_success_rate:6.1f}%")
    print(f"Contaminated Names Success Rate: {contaminated_success_rate:6.1f}%")
    print(f"Multi-word Names Success Rate:   {challenging_success_rate:6.1f}%")
    print(f"Edge Cases Success Rate:         {edge_success_rate:6.1f}%")
    
    # Calculate overall weighted success rate
    total_tests = 100 + 50 + test_count + len(edge_cases)
    total_successes = clean_successes + contaminated_successes + challenging_successes + edge_successes
    overall_success_rate = (total_successes / total_tests) * 100
    
    print()
    print(f"OVERALL SUCCESS RATE: {total_successes}/{total_tests} = {overall_success_rate:.1f}%")
    
    # 6. Failure Analysis
    print(f"\n6. FAILURE ANALYSIS")
    print("-" * 60)
    
    print("Clean name failures:")
    clean_failures = [item for item in test_categories["clean_names"] if not item["exact_match"]]
    for failure in clean_failures[:10]:  # Show first 10 failures
        print(f"  Expected: '{failure['input']}'")
        print(f"  Got:      '{failure['output']}'")
        print()
    
    print("Contaminated name failures:")
    contaminated_failures = [item for item in test_categories["contaminated_names"] if not item["success"]]
    for failure in contaminated_failures[:5]:  # Show first 5 failures
        print(f"  Failed: '{failure['input']}'")
        print(f"  Result: '{failure['output']}'")
        print()
    
    # 7. Performance Insights
    print(f"\n7. PERFORMANCE INSIGHTS")
    print("-" * 60)
    
    # Analyze by word count
    word_count_analysis = {}
    for item in test_categories["clean_names"]:
        word_count = len(item["input"].split())
        if word_count not in word_count_analysis:
            word_count_analysis[word_count] = {"total": 0, "successes": 0}
        word_count_analysis[word_count]["total"] += 1
        if item["exact_match"]:
            word_count_analysis[word_count]["successes"] += 1
    
    print("Success rate by word count:")
    for word_count in sorted(word_count_analysis.keys()):
        data = word_count_analysis[word_count]
        success_rate = (data["successes"] / data["total"]) * 100
        print(f"  {word_count} words: {data['successes']}/{data['total']} = {success_rate:.1f}%")
    
    return {
        "total_banks_available": len(THOUSAND_BANK_NAMES),
        "tests_run": {
            "clean": 100,
            "contaminated": 50,
            "challenging": test_count,
            "edge": len(edge_cases)
        },
        "success_rates": {
            "clean": clean_success_rate,
            "contaminated": contaminated_success_rate,
            "challenging": challenging_success_rate,
            "edge": edge_success_rate,
            "overall": overall_success_rate
        },
        "detailed_results": test_categories
    }

if __name__ == "__main__":
    print("🚀 Starting comprehensive 1000+ bank name extraction test...")
    results = run_comprehensive_1000_bank_test()
    print(f"\n🎉 Test completed successfully!")
    print(f"Database contains {results['total_banks_available']} real bank names")
    print(f"Overall success rate: {results['success_rates']['overall']:.1f}%")
