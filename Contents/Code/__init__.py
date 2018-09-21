####################################################################################################
#                                                                                                  #
#                                    BongaCams Plex Channel                                        #
#                                                                                                  #
####################################################################################################
from updater    import Updater
from DumbTools  import DumbKeyboard
from DumbTools  import DumbPrefs

from datetime   import datetime
from os.path    import abspath, exists

import json, time

PREFIX          = '/video/bongacams'
TITLE           = 'BongaCams'
ICON            = 'icon-default.png'
ICON_NEXT       = 'icon-nextpage.png'
ART             = 'art-default.jpg'

PAGESIZE        = 50
DEFAULT_SORT    = 'popular'
DEFAULT_GENDER  = 'female'

BASE_URL        = 'https://bongacams.com'
LISTING_URL     = BASE_URL + '/tools/listing_v3.php?online_only=true&offset={offset}&livetab={gender}&category={catgegory}&model_search%5Bper_page%5D={pagesize}&model_search%5Bbase_sort%5D={sort}&nc={unique}'

HEADERS         = {
    'Accept':'application/json',
    'Accept-Language':'en,en-US;q=0.7,en;q=0.3',
    'Content-Type':'application/x-www-form-urlencoded',
    'Origin':'{}'.format(BASE_URL),
    'Referer':'{}'.format(BASE_URL), 
    'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 8_1_3 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12B466 Safari/600.1.4', 
    'X-Requested-With':'XMLHttpRequest',
}

MAIN_LIST =     [
                    ('Women',       '/'), 
                    ('Men',         '/male'),
                    ('Couples',     '/couples'), 
                    ('Trans',       '/transsexual')
                ]

SORT_LIST =     [
                    ('Popular',         'popular'),
                    ('CamScore',        'camscore'),
                    ('Just Logged On',  'logged'),
                    ('New Models',      'new'),
                    ('Lovers',          'lovers'),
                ]

####################################################################################################

def Start():
    ObjectContainer.title1      = TITLE
    ObjectContainer.art         = R(ART)

    DirectoryObject.thumb       = R(ICON)
    DirectoryObject.art         = R(ART)

    InputDirectoryObject.art    = R(ART)

    VideoClipObject.thumb       = R(ICON)
    VideoClipObject.art         = R(ART)

    HTTP.CacheTime              = 0

####################################################################################################

@handler(PREFIX, TITLE, thumb=ICON, art=ART)
def MainMenu():
    oc = ObjectContainer(title2=TITLE, art=R(ART), no_cache=True)

    Updater(PREFIX + '/updater', oc)

    for (title, url) in MAIN_LIST:
        if title == 'Couples':
            oc.add(DirectoryObject(
                key     = Callback(SortList, title=title, url=url, gender='couples', category=''), 
                title   = title
            ))
        else:
            oc.add(DirectoryObject(
                key     = Callback(CategoryList, title=title, url=url), 
                title   = title
            ))

    return oc

####################################################################################################

@route(PREFIX + '/{title}/categories')
def CategoryList(title, url):
    oc          = ObjectContainer(title2=title, art=R(ART), no_cache=True)
    html        = HTML.ElementFromURL(BASE_URL+url)
    titleParent = title
    gender      = 'female' if url == '/' else url.split('/')[-1]

    oc.add(DirectoryObject(
        key     = Callback(SortList, title='All', url=url), 
        title   = 'All'
    ))

    for node in html.xpath('//div[@class="model_categories_panel"]//li'):
        title       = node.xpath(".//a/text()")[0]
        url         = node.xpath('.//a/@href')[0]
        total       = node.xpath('.//span/text()')[0]
        
        category    = url.split('/')[-1]

        if isinstance(total, int):
            total = int(total)

        titleCrumbs = '{} > {}'.format(titleParent, title)

        if title != 'All':
            title   = '{} ({})'.format(title, total)

        oc.add(DirectoryObject(
            key     = Callback(SortList, title=titleCrumbs, url=url, gender=gender, category=category), 
            title   = title
        ))                

    return oc

####################################################################################################

@route(PREFIX + '/sort')
def SortList(title, url, gender=DEFAULT_GENDER, category=''):
    oc          = ObjectContainer(title2=title, art=R(ART), no_cache=True)
    titleParent = title

    for (title, sort) in SORT_LIST:
        titleCrumbs = '{} > {}'.format(titleParent, title)

        oc.add(DirectoryObject(
            key     = Callback(CamList, title=titleCrumbs, url=url, gender=gender, category=category, sort=sort), 
            title   = 'Sort by {}'.format(title)
        ))

    return oc

####################################################################################################

@route(PREFIX + '/cams', page=int)
def CamList(title, url, page=1, gender=DEFAULT_GENDER, category='', sort=DEFAULT_SORT):
    oc              = ObjectContainer(title2=title, no_cache=True)
    cr              = '\r' if Client.Product == 'Plex Web' else '\n'

    pageOffset      = 0 if page == 1 else (page - 1) * PAGESIZE
    
    apiRequest      = LISTING_URL.format(
                            pagesize    = PAGESIZE,
                            offset      = pageOffset,
                            gender      = gender,
                            catgegory   = category,
                            sort        = sort,
                            unique      = time.time()
                      )
                      
    apiResponse     = HTTP.Request(apiRequest, headers=HEADERS).content
    metadataJson    = JSON.ObjectFromString(apiResponse)

    for cam in metadataJson['models']:
        camName         = cam["username"]
        camDisplayName  = cam["display_name"]
        camThumb        = cam["thumb_image"]
        camSummary      = cam["about_me"]

        if 'https:' not in camThumb:
            camThumb = 'https:' + camThumb

        oc.add(VideoClipObject(
            url     = '{}/{}'.format(BASE_URL, camName),
            thumb   = '{}?{}'.format(camThumb, time.time()),
            title   = camDisplayName,
            year    = datetime.now().year,
            summary = unicode(camSummary.strip()) if len(camSummary) > 0 else 'No summary',
            tagline = ''
        ))
    
    if len(oc) > 0:
        oc.add(DirectoryObject(
            key     = Callback(CamList, title=title, url=url, page=page+1, gender=gender, category=category, sort=sort),
            title   = 'Next Page',
            thumb   = R(ICON_NEXT)
        ))

        return oc

    return MessageContainer(header='Warning', message='Page Empty')
