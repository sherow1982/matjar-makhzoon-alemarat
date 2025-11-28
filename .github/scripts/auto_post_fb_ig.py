#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكربت النشر التلقائي على Facebook و Instagram
ينشر منتج كل 8 ساعات مع تتبع كامل
"""

import json
import random
import os
import sys
from datetime import datetime
import requests
from io import BytesIO
import xml.etree.ElementTree as ET
from urllib.parse import quote
import time

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
        with open('sitemap.xml', 'r', encoding='utf-8') as f:
            sitemap_content = f.read()
        
        root = ET.fromstring(sitemap_content)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        urls = []
        for url_element in root.findall('ns:url', namespace):
            loc = url_element.find('ns:loc', namespace)
            if loc is not None and loc.text:
                url = loc.text.strip()
                if '/products/' in url and url.endswith('.html'):
                    urls.append(url)
        
        print(f"✅ تم سحب {len(urls)} رابط من sitemap.xml")
        return urls
        
    except Exception as e:
        print(f"❌ خطأ في سحب الروابط: {e}")
        return []

# ========== استخراج ID من الرابط ==========
def extract_id_from_url(url):
    """استخراج product ID من الرابط"""
    try:
        filename = url.split('/products/')[-1]
        filename_without_ext = filename.replace('.html', '')
        parts = filename_without_ext.split('-')
        product_id = parts[-1]
        int(product_id)
        return product_id
    except:
        return None

# ========== تحويل URL encoding ==========
def encode_arabic_url(url):
    """تحويل الأحرف العربية لـ URL encoding"""
    try:
        if '/products/' in url:
            base = url.split('/products/')[0]
            filename = url.split('/products/')[1]
            encoded_filename = quote(filename, safe='-.')
            return f"{base}/products/{encoded_filename}"
        return url
    except:
        return url

# ========== بناء خريطة ID -> URL ==========
def build_id_to_url_map(urls):
    """بناء خريطة من product ID إلى URL"""
    id_to_url = {}
    for url in urls:
        product_id = extract_id_from_url(url)
        if product_id:
            encoded_url = encode_arabic_url(url)
            id_to_url[product_id] = encoded_url
    print(f"✅ تم بناء خريطة لـ {len(id_to_url)} منتج")
    return id_to_url

# ========== نظام التتبع ==========
def load_tracking():
    """تحميل ملف التتبع"""
    try:
        if os.path.exists('posted_products_fb_ig.json'):
            with open('posted_products_fb_ig.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"📊 التتبع: {len(data.get('posted', []))} منتج منشور في الدورة {data.get('cycle', 1)}")
                return data
    except:
        pass
    return {"posted": [], "cycle": 1}

def save_tracking(tracking):
    """حفظ ملف التتبع"""
    try:
        with open('posted_products_fb_ig.json', 'w', encoding='utf-8') as f:
            json.dump(tracking, f, ensure_ascii=False, indent=2)
        print(f"💾 تم حفظ التتبع: {len(tracking['posted'])} منتج")
    except Exception as e:
        print(f"⚠️ فشل حفظ التتبع: {e}")

def select_next_product(products, tracking, id_to_url):
    """اختيار المنتج التالي"""
    total = len(products)
    posted = set(tracking.get('posted', []))
    cycle = tracking.get('cycle', 1)
    
    print(f"\n🔍 البحث عن منتج جديد...")
    print(f"📊 تم نشر {len(posted)} منتج من {total} في الدورة {cycle}")
    
    available = []
    for p in products:
        product_id = str(p.get('id'))
        if product_id in posted:
            continue
        if product_id not in id_to_url:
            continue
        available.append({
            'product': p,
            'product_id': product_id,
            'url': id_to_url[product_id]
        })
    
    print(f"✅ وجدنا {len(available)} منتج متاح")
    
    if not available:
        print(f"\n🎉 انتهت الدورة {cycle}")
        print("🔄 بدء دورة جديدة...\n")
        tracking['posted'] = []
        tracking['cycle'] = cycle + 1
        save_tracking(tracking)
        return select_next_product(products, tracking, id_to_url)
    
    selected = random.choice(available)
    print(f"🎯 منتج مختار: {selected['product'].get('title', 'N/A')}")
    return selected['product'], selected['url']

# ========== تحميل الصورة ==========
def download_image(image_url):
    """تحميل الصورة"""
    try:
        response = requests.get(image_url, timeout=10)
        if response.status_code == 200:
            print(f"✅ تم تحميل الصورة")
            return response.content
        return None
    except Exception as e:
        print(f"❌ خطأ تحميل الصورة: {e}")
        return None

# ========== إنشاء محتوى المنشور ==========
def create_post_content(product, product_url):
    """إنشاء محتوى المنشور"""
    title = product.get('title', 'منتج جديد')
    price = product.get('price', 'N/A')
    image_url = product.get('image_link', '')
    
    emojis = ['✨', '🔥', '🛍️', '🎁', '⭐', '💥', '👑']
    emoji = random.choice(emojis)
    
    # محتوى للفيسبوك وإنستجرام
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

# ========== النشر على Facebook ==========
def post_to_facebook(content):
    """النشر على Facebook مع الصورة"""
    try:
        page_id = os.getenv('FACEBOOK_PAGE_ID')
        access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
        
        if not page_id or not access_token:
            print("⚠️ Facebook credentials missing")
            return False
        
        # تحميل الصورة
        image_data = None
        if content['image_url']:
            image_data = download_image(content['image_url'])
        
        if image_data:
            # نشر مع صورة
            url = f"https://graph.facebook.com/v18.0/{page_id}/photos"
            
            files = {
                'source': ('product.jpg', BytesIO(image_data), 'image/jpeg')
            }
            
            data = {
                'message': content['text'],
                'access_token': access_token
            }
            
            response = requests.post(url, files=files, data=data, timeout=30)
            
        else:
            # نشر نص فقط
            url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
            
            data = {
                'message': content['text'],
                'access_token': access_token
            }
            
            response = requests.post(url, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ تم النشر على Facebook: {result.get('id', 'N/A')}")
            return True
        else:
            print(f"❌ فشل Facebook: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ خطأ Facebook: {e}")
        import traceback
        traceback.print_exc()
        return False

# ========== النشر على Instagram ==========
def post_to_instagram(content):
    """النشر على Instagram مع الصورة"""
    try:
        account_id = os.getenv('INSTAGRAM_ACCOUNT_ID')
        access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
        
        if not account_id or not access_token:
            print("⚠️ Instagram credentials missing")
            return False
        
        if not content['image_url']:
            print("⚠️ Instagram يحتاج صورة")
            return False
        
        # خطوة 1: إنشاء container
        create_url = f"https://graph.facebook.com/v18.0/{account_id}/media"
        
        create_data = {
            'image_url': content['image_url'],
            'caption': content['text'],
            'access_token': access_token
        }
        
        create_response = requests.post(create_url, data=create_data, timeout=30)
        
        if create_response.status_code != 200:
            print(f"❌ فشل إنشاء container: {create_response.status_code}")
            print(f"Response: {create_response.text}")
            return False
        
        container_id = create_response.json().get('id')
        print(f"✅ تم إنشاء container: {container_id}")
        
        # انتظار قليل للمعالجة
        print("⏳ انتظار معالجة الصورة...")
        time.sleep(5)
        
        # خطوة 2: نشر container
        publish_url = f"https://graph.facebook.com/v18.0/{account_id}/media_publish"
        
        publish_data = {
            'creation_id': container_id,
            'access_token': access_token
        }
        
        publish_response = requests.post(publish_url, data=publish_data, timeout=30)
        
        if publish_response.status_code == 200:
            result = publish_response.json()
            print(f"✅ تم النشر على Instagram: {result.get('id', 'N/A')}")
            return True
        else:
            print(f"❌ فشل Instagram: {publish_response.status_code}")
            print(f"Response: {publish_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ خطأ Instagram: {e}")
        import traceback
        traceback.print_exc()
        return False

# ========== البرنامج الرئيسي ==========
def main():
    print("\n" + "="*50)
    print("🚀 بدء النشر على Facebook & Instagram")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50 + "\n")
    
    # 1. تحميل المنتجات
    products = load_products()
    if not products:
        print("❌ لا توجد منتجات")
        sys.exit(1)
    
    # 2. سحب الروابط
    product_urls = get_product_urls_from_sitemap()
    if not product_urls:
        print("❌ فشل سحب الروابط")
        sys.exit(1)
    
    # 3. بناء خريطة
    id_to_url = build_id_to_url_map(product_urls)
    if not id_to_url:
        print("❌ فشل بناء الخريطة")
        sys.exit(1)
    
    # 4. تحميل التتبع
    tracking = load_tracking()
    
    # 5. اختيار المنتج
    product, product_url = select_next_product(products, tracking, id_to_url)
    if not product:
        print("❌ فشل اختيار المنتج")
        sys.exit(1)
    
    print(f"\n📦 المنتج: {product.get('title', 'N/A')}")
    print(f"🆔 ID: {product.get('id')}")
    print(f"🔗 الرابط: {product_url}")
    print(f"🔢 الدورة: {tracking['cycle']}")
    print(f"✅ تم نشر: {len(tracking['posted'])}/{len(products)} منتج\n")
    
    # 6. إنشاء المحتوى
    content = create_post_content(product, product_url)
    print(f"\n📝 المحتوى:\n{content['text']}\n")
    
    # 7. النشر
    fb_success = post_to_facebook(content)
    ig_success = post_to_instagram(content)
    
    # 8. تحديث التتبع
    if fb_success or ig_success:
        product_id = str(product.get('id'))
        tracking['posted'].append(product_id)
        save_tracking(tracking)
        print(f"\n✅ تم تحديث التتبع: {len(tracking['posted'])}/{len(products)}")
    
    # 9. النتيجة
    print("\n" + "="*50)
    print("📊 النتيجة:")
    print(f"{'✅' if fb_success else '❌'} Facebook: {'Success' if fb_success else 'Failed'}")
    print(f"{'✅' if ig_success else '❌'} Instagram: {'Success' if ig_success else 'Failed'}")
    print("="*50 + "\n")
    
    # فشل إذا ما نجح أي منهم
    if not (fb_success or ig_success):
        sys.exit(1)

if __name__ == "__main__":
    main()
