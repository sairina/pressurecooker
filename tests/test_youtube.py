from pressurecooker import youtube

trees = {}
yt_resources = {}

cc_playlist = 'https://www.youtube.com/playlist?list=PL7m903CwFUgntbjkVMwts89fZq0INCtVS'
non_cc_playlist = 'https://www.youtube.com/playlist?list=PLBO8M-O_dTPE51ymDUgilf8DclGAEg9_A'
subtitles_video = 'https://www.youtube.com/watch?v=6uXAbJQoZlE'


def get_yt_resource(url):
    global yt_resources
    if not url in yt_resources:
        yt_resources[url] = youtube.YouTubeResource(url)

    return yt_resources[url]


def test_get_youtube_info():
    yt_resource = get_yt_resource(non_cc_playlist)
    tree = yt_resource.get_resource_info()
    assert tree['id']
    assert tree['kind']
    assert tree['title']
    assert len(tree['children']) == 4

    for video in tree['children']:
        assert video['id']
        assert video['kind']
        assert video['title']


def test_warnings_no_license():
    yt_resource = get_yt_resource(non_cc_playlist)
    issues, output_info = yt_resource.check_for_content_issues()

    assert len(issues) == 4
    for issue in issues:
        assert 'no_license_specified' in issue['warnings']


def test_cc_no_warnings():
    yt_resource = get_yt_resource(cc_playlist)
    issues, output_info = yt_resource.check_for_content_issues()

    # there is one video in this playlist that is not cc-licensed
    assert len(issues) == 1
    for issue in issues:
        assert 'no_license_specified' in issue['warnings']


def test_get_subtitles():
    yt_resource = get_yt_resource(subtitles_video)
    info = yt_resource.get_resource_subtitles()
    assert len(info['subtitles']) == 1
    assert 'ru' in info['subtitles']