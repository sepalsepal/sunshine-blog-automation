
def id_to_shortcode(media_id):
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
    shortcode = ''
    media_id = int(media_id)
    while media_id > 0:
        remainder = media_id % 64
        shortcode = alphabet[remainder] + shortcode
        media_id //= 64
    return shortcode

media_id = "18157404010415805"
print(f"Media ID: {media_id}")
print(f"Shortcode: {id_to_shortcode(media_id)}")
print(f"Correct URL: https://www.instagram.com/p/{id_to_shortcode(media_id)}/")
