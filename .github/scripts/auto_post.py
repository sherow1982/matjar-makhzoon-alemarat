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

# ========== سحب أسماء الملفات من الفولدر ==========
def get_product_filenames():
    """سحب أسماء ملفات HTML الفعلية من مجلد products/ باستخدام GitHub API مباشرة"""
    try:
        token = os.getenv('GITHUB_TOKEN')
        if not token:
            print("⚠️ GITHUB_TOKEN not found")
            return {}
        
        # استخدام GitHub API مباشرة
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        url = 'https://api.github.com/repos/sherow1982/matjar-makhzoon-alemarat/contents/products'
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ فشل الاتصال بـ GitHub API: {response.status_code}")
            return {}
        
        contents = response.json()
        
        # بناء خريطة من id -> اسم الملف الكامل
        id_to_filename = {}
        for file in contents:
            if file['name'].endswith('.html'):
                # استخراج الـ ID من نهاية اسم الملف (قبل .html)
                # مثال: "منظم-ادراج-المطبخ-5.html" -> ID = 5
                filename_without_ext = file['name'][:-5]  # إزالة .html
                parts = filename_without_ext.split('-')
                
                # آخر جزء هو الـ ID
                try:
                    product_id = parts[-1]
                    # تأكد أنه رقم
                    int(product_id)
                    # حفظ: ID -> اسم الملف الكامل
                    id_to_filename[product_id] = file['name']
                except (ValueError, IndexError):
                    # لو ما قدر يستخرج ID، تخطى
                    continue
        
        print(f"✅ تم سحب {len(id_to_filename)} ملف من المجلد")
        if id_to_filename:
            print(f"📋 عينة: {list(id_to_filename.items())[:3]}")
        return id_to_filename
        
    except Exception as e:
        print(f"❌ خطأ في سحب أسماء الملفات: {e}")
        import traceback
        traceback.print_exc()
        return {}

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

def select_next_product(products, tracking, filenames):
    """اختيار المنتج التالي حسب نظام التتبع - ما ينشر منتج مرتين في نفس الدورة"""
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
        
        # تحقق: هل المنتج له ملف في الفولدر؟
        if product_id not in filenames:
            continue
        
        # منتج متاح للنشر
        available.append({
            'product': p,
            'product_id': product_id,
            'filename': filenames[product_id]
        })
    
    print(f"✅ وجدنا {len(available)} منتج متاح للنشر")
    
    # إذا خلصت كل المنتجات، ابدأ دورة جديدة
    if not available:
        print(f"\n🎉 انتهت الدورة {cycle} - تم نشر {len(posted)}/{total} منتج")
        print("🔄 بدء دورة جديدة...\n")
        tracking['posted'] = []
        tracking['cycle'] = cycle + 1
        save_tracking(tracking)
        return select_next_product(products, tracking, filenames)
    
    # اختيار منتج عشوائي من المتاحين
    selected = random.choice(available)
    print(f"🎯 تم اختيار المنتج: {selected['product'].get('title', 'N/A')}")
    print(f"📄 الملف: {selected['filename']}")
    
    return selected['product'], selected['filename']

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
def create_post_content(product, filename):
    """إنشاء محتوى المنشور مع الصورة - استخدام اسم الملف الفعلي بالكامل"""
    title = product.get('title', 'منتج جديد')
    price = product.get('price', 'N/A')
    image_url = product.get('image_link', '')
    
    # بناء رابط المنتج من اسم الملف الفعلي الكامل (بدون أي تعديل)
    base_url = 'https://sherow1982.github.io/matjar-makhzoon-alemarat'
    product_url = f"{base_url}/products/{filename}"
    
    print(f"🔗 الرابط المبني: {product_url}")
    
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
    
    # 2. سحب أسماء الملفات من الفولدر
    filenames = get_product_filenames()
    if not filenames:
        print("❌ فشل سحب أسماء الملفات من الفولدر")
        sys.exit(1)
    
    # 3. تحميل نظام التتبع
    tracking = load_tracking()
    
    # 4. اختيار المنتج التالي
    product, filename = select_next_product(products, tracking, filenames)
    if not product:
        print("❌ فشل اختيار المنتج")
        sys.exit(1)
    
    print(f"\n📦 المنتج المختار: {product.get('title', 'N/A')}")
    print(f"🆔 ID: {product.get('id')}")
    print(f"📄 الملف: {filename}")
    print(f"🔢 الدورة: {tracking['cycle']}")
    print(f"✅ تم نشر: {len(tracking['posted'])}/{len(products)} منتج\n")
    
    # 5. إنشاء المحتوى
    content = create_post_content(product, filename)
    print(f"\n📝 المحتوى:\n{content['text']}")
    print(f"🔗 رابط المنتج: {content['url']}")
    print(f"🖼️ الصورة: {content['image_url'][:80]}...\n")
    
    # 6. النشر على Twitter فقط
    success = post_to_twitter(content)
    
    # 7. تحديث نظام التتبع
    if success:
        product_id = str(product.get('id'))
        tracking['posted'].append(product_id)
        save_tracking(tracking)
        print(f"\n✅ تم تحديث التتبع: {len(tracking['posted'])}/{len(products)}")
        print(f"📝 المنتج {product_id} تم إضافته لقائمة المنشورات")
    
    # 8. النتيجة
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
