#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكربت النشر التلقائي على Twitter فقط
ينشر منتج كل 8 ساعات مع تتبع كامل - ما يكرر منتج إلا بعد ما يخلص الـ 882 منتج كلهم
"""

import json
import random
import os
import sys
from datetime import datetime
import requests
from io import BytesIO
import xml.etree.ElementTree as ET

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

# ========== سحب الروابط من sitemap.xml ==========
def get_product_urls_from_sitemap():
    """سحب روابط المنتجات مباشرة من sitemap.xml"""
    try:
        # قراءة ملف sitemap.xml
        with open('sitemap.xml', 'r', encoding='utf-8') as f:
            sitemap_content = f.read()
        
        # Parse XML
        root = ET.fromstring(sitemap_content)
        
        # النمسبيس الخاص بـ sitemap
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        # سحب كل الروابط من <loc>
        urls = []
        for url_element in root.findall('ns:url', namespace):
            loc = url_element.find('ns:loc', namespace)
            if loc is not None and loc.text:
                url = loc.text.strip()
                # فقط روابط المنتجات (اللي فيها /products/)
                if '/products/' in url and url.endswith('.html'):
                    urls.append(url)
        
        print(f"✅ تم سحب {len(urls)} رابط من sitemap.xml")
        
        if urls:
            print(f"📋 عينة: {urls[:3]}")
        
        return urls
        
    except Exception as e:
        print(f"❌ خطأ في سحب الروابط من sitemap.xml: {e}")
        import traceback
        traceback.print_exc()
        return []

# ========== استخراج ID من الرابط ==========
def extract_id_from_url(url):
    """استخراج product ID من الرابط
    مثال: .../products/جهاز-مساج-لتدليك-فروة-الرأس-1.html -> 1
    """
    try:
        # استخراج اسم الملف من الرابط
        filename = url.split('/products/')[-1]
        # إزالة .html
        filename_without_ext = filename.replace('.html', '')
        # آخر جزء بعد شرطة هو الـ ID
        parts = filename_without_ext.split('-')
        product_id = parts[-1]
        # تأكد أنه رقم
        int(product_id)
        return product_id
    except:
        return None

# ========== بناء خريطة ID -> URL ==========
def build_id_to_url_map(urls):
    """بناء خريطة من product ID إلى URL الكامل"""
    id_to_url = {}
    
    for url in urls:
        product_id = extract_id_from_url(url)
        if product_id:
            id_to_url[product_id] = url
    
    print(f"✅ تم بناء خريطة لـ {len(id_to_url)} منتج")
    return id_to_url

# ========== نظام التتبع ==========
def load_tracking():
    """تحميل ملف التتبع"""
    try:
        if os.path.exists('posted_products.json'):
            with open('posted_products.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"📊 التتبع الحالي: {len(data.get('posted', []))} منتج منشور في الدورة {data.get('cycle', 1)}")
                return data
    except:
        pass
    return {"posted": [], "cycle": 1}

def save_tracking(tracking):
    """حفظ ملف التتبع"""
    try:
        with open('posted_products.json', 'w', encoding='utf-8') as f:
            json.dump(tracking, f, ensure_ascii=False, indent=2)
        print(f"💾 تم حفظ التتبع: {len(tracking['posted'])} منتج")
    except Exception as e:
        print(f"⚠️ فشل حفظ التتبع: {e}")

def select_next_product(products, tracking, id_to_url):
    """اختيار المنتج التالي حسب ننظام التتبع - ما ينشر منتج مرتين في نفس الدورة"""
    total = len(products)
    posted = set(tracking.get('posted', []))  # استخدام set للبحث السريع
    cycle = tracking.get('cycle', 1)
    
    print(f"\n🔍 البحث عن منتج جديد...")
    print(f"📊 تم نشر {len(posted)} منتج من {total} في الدورة {cycle}")
    
    # إنشاء قائمة بالمنتجات الغير منشورة
    available = []
    for p in products:
        product_id = str(p.get('id'))
        
        # تحقق: هل المنتج منشور في الدورة الحالية؟
        if product_id in posted:
            continue  # تخطى - منشور بالفعل
        
        # تحقق: هل المنتج له رابط في السايت ماب؟
        if product_id not in id_to_url:
            continue
        
        # منتج متاح للنشر
        available.append({
            'product': p,
            'product_id': product_id,
            'url': id_to_url[product_id]
        })
    
    print(f"✅ وجدنا {len(available)} منتج متاح للنشر")
    
    # إذا خلصت كل المنتجات، ابدأ دورة جديدة
    if not available:
        print(f"\n🎉 انتهت الدورة {cycle} - تم نشر {len(posted)}/{total} منتج")
        print("🔄 بدء دورة جديدة...\n")
        tracking['posted'] = []
        tracking['cycle'] = cycle + 1
        save_tracking(tracking)
        return select_next_product(products, tracking, id_to_url)
    
    # اختيار منتج عشوائي من المتاحين
    selected = random.choice(available)
    print(f"🎯 تم اختيار المنتج: {selected['product'].get('title', 'N/A')}")
    print(f"🔗 الرابط: {selected['url']}")
    
    return selected['product'], selected['url']

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
def create_post_content(product, product_url):
    """إنشاء محتوى المنشور مع الصورة - استخدام الرابط من sitemap.xml مباشرة"""
    title = product.get('title', 'منتج جديد')
    price = product.get('price', 'N/A')
    image_url = product.get('image_link', '')
    
    # الرابط مباشرة من sitemap.xml
    print(f"🔗 الرابط من sitemap: {product_url}")
    
    # محتوى المنشور
    emojis = ['✨', '🔥', '🛍', '🎁', '⭐', '💥', '👑']
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
        import traceback
        traceback.print_exc()
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
    
    # 2. سحب الروابط من sitemap.xml
    product_urls = get_product_urls_from_sitemap()
    if not product_urls:
        print("❌ فشل سحب الروابط من sitemap.xml")
        sys.exit(1)
    
    # 3. بناء خريطة ID -> URL
    id_to_url = build_id_to_url_map(product_urls)
    if not id_to_url:
        print("❌ فشل بناء خريطة الروابط")
        sys.exit(1)
    
    # 4. تحميل نظام التتبع
    tracking = load_tracking()
    
    # 5. اختيار المنتج التالي
    product, product_url = select_next_product(products, tracking, id_to_url)
    if not product:
        print("❌ فشل اختيار المنتج")
        sys.exit(1)
    
    print(f"\n📦 المنتج المختار: {product.get('title', 'N/A')}")
    print(f"🆔 ID: {product.get('id')}")
    print(f"🔗 الرابط: {product_url}")
    print(f"🔢 الدورة: {tracking['cycle']}")
    print(f"✅ تم نشر: {len(tracking['posted'])}/{len(products)} منتج\n")
    
    # 6. إنشاء المحتوى
    content = create_post_content(product, product_url)
    print(f"\n📝 المحتوى:\n{content['text']}")
    print(f"🔗 رابط المنتج: {content['url']}")
    print(f"🖼️ الصورة: {content['image_url'][:80]}...\n")
    
    # 7. النشر على Twitter فقط
    success = post_to_twitter(content)
    
    # 8. تحديث نظام التتبع
    if success:
        product_id = str(product.get('id'))
        tracking['posted'].append(product_id)
        save_tracking(tracking)
        print(f"\n✅ تم تحديث التتبع: {len(tracking['posted'])}/{len(products)}")
        print(f"📝 المنتج {product_id} تم إضافته لقائمة المنشورات")
    
    # 9. النتيجة
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
