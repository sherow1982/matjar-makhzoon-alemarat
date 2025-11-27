#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكربت النشر التلقائي على Twitter فقط
يسحب منتج عشوائي وينشر (الاسم + السعر + رابط المنتج + الصورة)
"""

import json
import random
import os
import sys
from datetime import datetime
import requests
from io import BytesIO
from urllib.parse import quote

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
    product_id = product.get('id', '')
    image_url = product.get('image_link', '')
    
    # بناء رابط المنتج من مجلد products - URL encoding للـ id
    base_url = 'https://sherow1982.github.io/matjar-makhzoon-alemarat'
    product_url = f"{base_url}/products/{quote(product_id)}.html"
    
    # محتوى المنشور
    emojis = ['✨', '🔥', '🛒', '🎁', '⭐', '💥', '👑']
    emoji = random.choice(emojis)
    
    post_text = f"""{emoji} {title}

💰 السعر: {price} درهم
🚚 شحن مجاني لجميع الإمارات
📞 للطلب: +20 111 076 0081

👉 {product_url}

#متجر_مخزون_الإمارات #تسوق_الامارات #دبي #الشارقة #عروض"""
    
    return {
        'text': post_text,
        'url': product_url,
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

# ========== البرنامج الرئيسي ==========
def main():
    print("\n" + "="*50)
    print("🚀 بدء النشر التلقائي على Twitter")
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
    print(f"🔗 رابط المنتج: {content['url']}")
    print(f"🖼️ الصورة: {content['image_url'][:80]}...\n")
    
    # 4. النشر على Twitter فقط
    success = post_to_twitter(content)
    
    # 5. النتيجة
    print("\n" + "="*50)
    print("📊 النتيجة:")
    status = "✅" if success else "❌"
    print(f"{status} Twitter: {'Success' if success else 'Failed'}")
    print("="*50 + "\n")
    
    # Exit with error if failed
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
