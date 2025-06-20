from bs4 import BeautifulSoup

def parse_album_page_for_spotify_link(html_content: str) -> str | None:
    """Parses the album page HTML to find the Spotify link."""
    soup = BeautifulSoup(html_content, 'lxml')
    spotify_link_tag = soup.find('a', class_='spotify_link')
    if spotify_link_tag and spotify_link_tag.has_attr('href'):
        return spotify_link_tag['href']
    return None

def parse_list_page_for_items(html_content: str) -> list[dict]:
    """Parses the main list page HTML to extract albums and songs."""
    soup = BeautifulSoup(html_content, 'lxml')
    results = []
    table = soup.find("table", id="user_list")
    if not table:
        return results

    base_url = "https://rateyourmusic.com"
    table_rows = table.find("tbody").find_all("tr")

    for row in table_rows:
        main_entry_cell = row.find("td", class_="main_entry")
        if not main_entry_cell:
            continue

        item = {}

        # Check for album
        artist_h2 = main_entry_cell.find("h2")
        album_h3 = main_entry_cell.find("h3")
        artist_link_tag = artist_h2.find("a", class_="list_artist") if artist_h2 else None
        album_link_tag = album_h3.find("a", class_="list_album") if album_h3 else None

        if artist_link_tag and album_link_tag:
            item['type'] = 'album'
            item['artist'] = artist_link_tag.get_text(strip=True)
            item['title'] = album_link_tag.get_text(strip=True)
            item['title_link'] = f"{base_url}{album_link_tag['href']}"
            results.append(item)
            continue

        # Check for song
        song_h2 = main_entry_cell.find("h2", class_="list_song")
        song_artist_h3 = main_entry_cell.find("h3", class_="list_song_artists")

        if song_h2 and song_artist_h3:
            song_link_tag = song_h2.find('a')
            song_artist_link_tag = song_artist_h3.find('a')

            if song_link_tag and song_artist_link_tag:
                item['type'] = 'song'
                item['title'] = song_link_tag.get_text(strip=True)
                item['artist'] = song_artist_link_tag.get_text(strip=True)
                results.append(item)

    return results