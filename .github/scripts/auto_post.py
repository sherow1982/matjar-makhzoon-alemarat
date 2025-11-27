#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكربت النشر التلقائي للمنتجات مع الصور
يسحب منتج عشوائي وينشر (الاسم + السعر + الرابط + الصورة)
"""

import json
import random
import os
import sys
from datetime import datetime
import requests
from io import BytesIO

# ========== تحميل المنتجات ==========
def load_products():
    """تحميل المنتجات من products.json"""
    try:
        with open('products.json', 'r', encoding='utf-8') as f:
            products = json.load(f)
        print(f"✅ تم تحميل {len(products)} منتج")
        return products
    except Exception as e:
        print(f"❌ خطأ في تحميل المنتجات: {e}")
        return []

# ========== اختيار منتج عشوائي ==========
def select_random_product(products):
    """اختيار منتج عشوائي له صورة"""
    # فلترة المنتجات اللي عندها صور
    products_with_images = [p for p in products if p.get('image_link')]
    
    if not products_with_images:
        print("⚠️ لا توجد منتجات بصور - استخدام كل المنتجات")
        products_with_images = products
    
    product = random.choice(products_with_images)
    print(f"✅ تم اختيار: {product.get('title', 'N/A')}")
    return product

# ========== تحميل الصورة ==========
def download_image(image_url):
    """تحميل الصورة من رابطها"""
    try:
        response = requests.get(image_url, timeout=10)
        if response.status_code == 200:
            print(f"✅ تم تحميل الصورة")
            return BytesIO(response.content)
        else:
            print(f"❌ فشل تحميل الصورة: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ خطأ تحميل الصورة: {e}")
        return None

# ========== إنشاء محتوى المنشور ==========
def create_post_content(product):
    """إنشاء محتوى المنشور مع الصورة"""
    title = product.get('title', 'منتج جديد')
    price = product.get('price', 'N/A')
    url = product.get('link', 'https://sherow1982.github.io/matjar-makhzoon-alemarat/')
    image_url = product.get('image_link', '')
    
    # محتوى المنشور
    emojis = ['✨', '🔥', '🛒', '🎁', '⭐', '💥', '👑']
    emoji = random.choice(emojis)
    
    post_text = f"""{emoji} {title}

💰 السعر: {price} درهم
🚚 شحن مجاني لجميع الإمارات
📞 للطلب: +20 111 076 0081

👉 {url}

#متجر_مخزون_الإمارات #تسوق_الامارات #دبي #الشارقة #عروض"""
    
    return {
        'text': post_text,
        'url': url,
        'image_url': image_url,
        'title': title
    }

# ========== النشر على Twitter ==========
def post_to_twitter(content):
    """النشر على Twitter/X مع الصورة"""
    try:
        import tweepy
        
        api_key = os.getenv('TWITTER_API_KEY')
        api_secret = os.getenv('TWITTER_API_SECRET')
        access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        access_secret = os.getenv('TWITTER_ACCESS_SECRET')
        
        if not all([api_key, api_secret, access_token, access_secret]):
            print("⚠️ Twitter API keys missing")
            return False
        
        # مصادقة API v1.1 لرفع الصور
        auth = tweepy.OAuth1UserHandler(
            api_key, api_secret,
            access_token, access_secret
        )
        api_v1 = tweepy.API(auth)
        
        # API v2 للتغريدات
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret
        )
        
        media_id = None
        
        # رفع الصورة إذا موجودة
        if content['image_url']:
            image_data = download_image(content['image_url'])
            if image_data:
                media = api_v1.media_upload(filename='product.jpg', file=image_data)
                media_id = media.media_id
                print(f"✅ تم رفع الصورة على Twitter")
        
        # نشر التغريدة
        if media_id:
            response = client.create_tweet(text=content['text'], media_ids=[media_id])
        else:
            response = client.create_tweet(text=content['text'])
        
        print(f"✅ تم النشر على Twitter: {response.data['id']}")
        return True
        
    except Exception as e:
        print(f"❌ خطأ Twitter: {e}")
        return False

# ========== النشر على Facebook ==========
def post_to_facebook(content):
    """النشر على Facebook Page مع الصورة"""
    try:
        page_id = os.getenv('FACEBOOK_PAGE_ID')
        access_token = os.getenv('FACEBOOK_PAGE_TOKEN')
        
        if not all([page_id, access_token]):
            print("⚠️ Facebook credentials missing")
            return False
        
        # نشر مع صورة
        if content['image_url']:
            url = f"https://graph.facebook.com/v18.0/{page_id}/photos"
            data = {
                'message': content['text'],
                'url': content['image_url'],  # رابط الصورة مباشرة
                'access_token': access_token
            }
        else:
            # نشر نصي بدون صورة
            url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
            data = {
                'message': content['text'],
                'link': content['url'],
                'access_token': access_token
            }
        
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            print(f"✅ تم النشر على Facebook: {response.json().get('id')}")
            return True
        else:
            print(f"❌ خطأ Facebook: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ خطأ Facebook: {e}")
        return False

# ========== النشر على Instagram ==========
def post_to_instagram(content):
    """النشر على Instagram مع الصورة"""
    try:
        from instagrapi import Client
        
        username = os.getenv('INSTAGRAM_USERNAME')
        password = os.getenv('INSTAGRAM_PASSWORD')
        
        if not all([username, password]):
            print("⚠️ Instagram credentials missing")
            return False
        
        if not content['image_url']:
            print("⚠️ لا توجد صورة لInstagram")
            return False
        
        cl = Client()
        cl.login(username, password)
        
        # تحميل ورفع الصورة
        image_data = download_image(content['image_url'])
        if not image_data:
            return False
        
        # حفظ مؤقت
        temp_path = '/tmp/product_image.jpg'
        with open(temp_path, 'wb') as f:
            f.write(image_data.read())
        
        # رفع على Instagram
        media = cl.photo_upload(
            temp_path,
            content['text']
        )
        
        print(f"✅ تم النشر على Instagram: {media.pk}")
        return True
        
    except Exception as e:
        print(f"❌ خطأ Instagram: {e}")
        return False

# ========== البرنامج الرئيسي ==========
def main():
    print("\n" + "="*50)
    print("🚀 بدء النشر التلقائي مع الصور")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50 + "\n")
    
    # 1. تحميل المنتجات
    products = load_products()
    if not products:
        print("❌ لا توجد منتجات")
        sys.exit(1)
    
    # 2. اختيار منتج
    product = select_random_product(products)
    if not product:
        print("❌ فشل اختيار المنتج")
        sys.exit(1)
    
    # 3. إنشاء المحتوى
    content = create_post_content(product)
    print(f"\n📝 المحتوى:\n{content['text']}")
    print(f"🖼️ الصورة: {content['image_url'][:80]}...\n")
    
    # 4. النشر
    results = {
        'twitter': post_to_twitter(content),
        'facebook': post_to_facebook(content),
        'instagram': post_to_instagram(content)
    }
    
    # 5. النتيجة
    print("\n" + "="*50)
    print("📊 النتائج:")
    for platform, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {platform.capitalize()}: {'Success' if success else 'Failed'}")
    print("="*50 + "\n")
    
    # Exit with error if all failed
    if not any(results.values()):
        sys.exit(1)

if __name__ == "__main__":
    main()
