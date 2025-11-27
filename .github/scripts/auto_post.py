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
    """سحب أسماء ملفات HTML الفعلية من مجلد products/"""
    try:
        from github import Github
        
        token = os.getenv('GITHUB_TOKEN')
        if not token:
            print("⚠️ GITHUB_TOKEN not found")
            return {}
        
        g = Github(token)
        repo = g.get_repo('sherow1982/matjar-makhzoon-alemarat')
        contents = repo.get_contents('products')
        
        # بناء خريطة من id -> اسم الملف
        id_to_filename = {}
        for file in contents:
            if file.name.endswith('.html'):
                # استخرج الـ id من اسم الملف (بدون .html)
                filename = file.name[:-5]  # إزالة .html
                # الـ id ممكن يكون في النهاية أو جزء من الاسم
                # نحفظ الـ filename كامل
                id_to_filename[filename] = file.name
        
        print(f"✅ تم سحب {len(id_to_filename)} ملف من المجلد")
        return id_to_filename
        
    except Exception as e:
        print(f"❌ خطأ في سحب أسماء الملفات: {e}")
        return {}

# ========== نظام التتبع ==========
def load_tracking():
    """تحميل ملف التتبع"""
    try:
        if os.path.exists('posted_products.json'):
            with open('posted_products.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {"posted": [], "cycle": 1}

def save_tracking(tracking):
    """حفظ ملف التتبع"""
    try:
        with open('posted_products.json', 'w', encoding='utf-8') as f:
            json.dump(tracking, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ فشل حفظ التتبع: {e}")

def select_next_product(products, tracking, filenames):
    """اختيار المنتج التالي حسب نظام التتبع"""
    total = len(products)
    posted = tracking.get('posted', [])
    cycle = tracking.get('cycle', 1)
    
    # إنشاء قائمة بالمنتجات الغير منشورة
    available = []
    for p in products:
        product_id = str(p.get('id'))
        # تحقق إذا المنتج له ملف في الفولدر
        has_file = False
        matching_filename = None
        for fname in filenames:
            if fname.startswith(product_id) or fname.endswith(f"-{product_id}"):
                has_file = True
                matching_filename = filenames[fname]
                break
        
        if has_file and product_id not in posted:
            available.append({
                'product': p,
                'filename': matching_filename
            })
    
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
    """إنشاء محتوى المنشور مع الصورة"""
    title = product.get('title', 'منتج جديد')
    price = product.get('price', 'N/A')
    image_url = product.get('image_link', '')
    
    # بناء رابط المنتج من اسم الملف الفعلي
    base_url = 'https://sherow1982.github.io/matjar-makhzoon-alemarat'
    product_url = f"{base_url}/products/{filename}"
    
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
    
    # 2. سحب أسماء الملفات من الفولدر
    filenames = get_product_filenames()
    if not filenames:
        print("⚠️ لم يتم العثور على ملفات - استخدام النظام القديم")
        # Fallback: استخدام id مباشرة
        filenames = {str(p['id']): f"{p['id']}.html" for p in products}
    
    # 3. تحميل نظام التتبع
    tracking = load_tracking()
    
    # 4. اختيار المنتج التالي
    product, filename = select_next_product(products, tracking, filenames)
    if not product:
        print("❌ فشل اختيار المنتج")
        sys.exit(1)
    
    print(f"📦 المنتج المختار: {product.get('title', 'N/A')}")
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
        tracking['posted'].append(str(product.get('id')))
        save_tracking(tracking)
        print(f"\n✅ تم تحديث التتبع: {len(tracking['posted'])}/{len(products)}")
    
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
