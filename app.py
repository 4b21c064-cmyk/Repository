# 導入必要的 Python 套件
from flask import Flask, send_file, request, jsonify
# Flask: 網頁應用程式框架

from roboflow import Roboflow
import cv2
import numpy as np
import requests
import os
from werkzeug.utils import secure_filename

# 建立 Flask 應用程式實例
app = Flask(__name__)

# 在終端機顯示啟動訊息
print("\n" + "=" * 60)
print("🎥 正在初始化系統...")
print("=" * 60)

# 初始化全域變數
# 儲存模型可以偵測的所有類別名稱
model_classes = []

# Roboflow 模型物件（用於執行偵測）
model = None

# 如果模型載入失敗，儲存錯誤訊息
model_error = None


# 設定檔案上傳資料夾
UPLOAD_FOLDER = 'uploads'

# 檢查資料夾是否存在，不存在則建立
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 初始化 Roboflow AI 模型
try:
    # 連接 Roboflow API
    print("🔄 正在連接 Roboflow API...")
    
    # ⭐ 重要：請替換成你自己的 API Key
    rf = Roboflow(api_key="QfGdvPSJPzstvleVYVJJ")
    
    print("✅ API 連接成功")

    # 載入專案
    print("🔄 正在載入專案...")
    
    # 指定工作區（workspace）和專案（project）名稱
    project = rf.workspace("loo-7pi0u").project("bacteria-ol8ci")
    
    print("✅ 專案載入成功")
    
    # 載入模型版本
    print("🔄 正在載入模型版本...")
    
    # 指定要使用的模型版本
    # ⭐ 每次在 Roboflow 重新訓練模型，版本號會增加
    version = project.version(6)
    
    print("✅ 版本載入成功")
    
    # 初始化模型物件
    print("🔄 正在初始化模型...")
    
    # 取得模型物件，之後用 model.predict() 執行偵測
    model = version.model
    
    print("✅ 模型初始化成功")


    # 自動獲取類別清單
    try:
        print("🔄 正在獲取類別清單...")
        
        # 建立 API 請求 URL
        # ⭐ 請修改成你的專案資訊：
        # url = f"https://api.roboflow.com/你的工作區/你的專案/你的版本號"
        url = f"https://api.roboflow.com/loo-7pi0u/bacteria-ol8ci/6"
        
        # 設定 API 參數（需要 API Key 驗證）
        params = {"api_key": "QfGdvPSJPzstvleVYVJJ"}
        
        response = requests.get(url, params=params, timeout=10)
        
        # 檢查 API 回應狀態
        if response.status_code == 200:
            data = response.json()
            
            # 檢查回應資料結構是否正確
            if 'version' in data and 'classes' in data['version']:
                # 提取類別名稱（字典的 keys）
                # 例如：['RBC', 'WBC', 'Candida', ...]
                model_classes = list(data['version']['classes'].keys())
                
                print(f"✅ 自動獲取到 {len(model_classes)} 個類別: {model_classes}")
                
            else:
                # 資料結構異常，使用預設類別
                print("⚠️  API 回應格式異常，使用預設類別")
                
                # 預設的細菌類別清單
                model_classes = [
                    'RBC',                  # 紅血球
                    'WBC',                  # 白血球
                    'Candida',              # 念珠菌
                    'Escherichia coli',     # 大腸桿菌
                    'Epithelial Cells',     # 上皮細胞
                    'SA',                   # 葡萄球菌
                    'Klebsiella',           # 克雷伯氏菌
                    'Urine Crystals'        # 尿結晶
                ]
                
        else:
            print(f"⚠️  API 回應錯誤 (狀態碼: {response.status_code})，使用預設類別")
            
            # 使用預設類別作為備援
            model_classes = [
                'RBC', 'WBC', 'Candida', 'Escherichia coli', 
                'Epithelial Cells', 'SA', 'Klebsiella', 'Urine Crystals'
            ]
            
            
    except Exception as e:
        # 網路錯誤、逾時等異常狀況
        print(f"⚠️  獲取類別清單失敗: {e}")
        
        # 使用預設類別確保系統可用
        model_classes = [
            'RBC', 'WBC', 'Candida', 'Escherichia coli', 
            'Epithelial Cells', 'SA', 'Klebsiella', 'Urine Crystals'
        ]
    
    # 顯示最終使用的類別清單
    print("📋 最終類別清單:", model_classes)


# 模型載入失敗的例外處理
except Exception as e:
    # 儲存錯誤訊息（供前端查詢）
    model_error = str(e)
    
    # 在終端機顯示詳細錯誤資訊
    print(f"\n❌ ❌ ❌ Roboflow 初始化失敗 ❌ ❌ ❌")
    print(f"錯誤訊息: {e}")
    print(f"錯誤類型: {type(e).__name__}")
    
    # 提供可能的解決方案
    print("\n可能的原因：")
    print("  1. API Key 無效或過期")
    print("     → 解決方法：到 Roboflow Dashboard 重新取得 API Key")
    print("  2. 網路連線問題")
    print("     → 解決方法：檢查網路連線，確認可以訪問 api.roboflow.com")
    print("  3. Roboflow 專案不存在或無權限")
    print("     → 解決方法：確認專案名稱和工作區名稱正確")
    print("  4. Roboflow 套件版本問題")
    print("     → 解決方法：執行 pip install --upgrade roboflow")
    print("\n請檢查以上問題後重新啟動程式")
    print("=" * 60 + "\n")
    
    # 即使模型載入失敗，也要設定預設類別
    model_classes = [
        'RBC', 'WBC', 'Candida', 'Escherichia coli', 
        'Epithelial Cells', 'SA', 'Klebsiella', 'Urine Crystals'
    ]
    # 靜態檔案路由：提供 HTML、CSS、JS 檔案
# 路由 1：首頁（index.html）
@app.route('/')
def index():
    """
    當使用者訪問 http://127.0.0.1:5000/ 時
    返回 index.html 檔案
    """
    return send_file('index.html')

# 路由 2：CSS 樣式表
@app.route('/style.css')
def style():
    """
    當前端請求 /style.css 時
    返回 style.css 檔案
    """
    return send_file('style.css')

# 路由 3：JavaScript 程式碼
@app.route('/script.js')
def script():
    """
    當前端請求 /script.js 時
    返回 script.js 檔案
    """
    return send_file('script.js')

# 取得模型類別清單
@app.route('/classes')
def get_classes():
    return jsonify(model_classes)


# 檢查模型狀態
@app.route('/model_status')
def model_status():
    return jsonify({
        # 模型是否成功載入（True/False）
        'model_ready': model is not None,
        # 錯誤訊息（如果有的話）
        'error': model_error,
        # 類別數量
        'classes_count': len(model_classes)
    })
    
# API 端點：執行 AI 偵測（Windows 版本）
@app.route('/detect', methods=['POST'])
def detect():  
    try:
        # 檢查模型是否就緒
        if model is None:
            # 模型未載入，建立錯誤訊息
            error_msg = f"Roboflow 模型未初始化"
            
            # 如果有詳細錯誤訊息，附加上去
            if model_error:
                error_msg += f": {model_error}"
            
            # 在終端機顯示錯誤
            print(f"❌ {error_msg}")
            
            # 返回 JSON 錯誤回應
            return jsonify({
                'success': False,           # 偵測失敗
                'error': error_msg,         # 錯誤訊息
                'suggestion': '請檢查後端控制台的錯誤訊息，並確認 Roboflow API Key 是否有效'
            })
        
        
        # 檢查是否有上傳檔案
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': '沒有上傳圖片'
            })
        
        # 取得上傳的檔案物件
        file = request.files['image']
        
        # 檢查檔案名稱是否為空
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': '檔案名稱為空'
            })
        
        
        # 儲存上傳的圖片（Windows 安全處理）
        filename = secure_filename('temp_frame.jpg')
        
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # 儲存檔案到硬碟
        file.save(filepath)
        
        # 在終端機顯示檔案大小（用於偵錯）
        print(f"📸 收到圖片，大小: {os.path.getsize(filepath)} bytes")
        
        
        # 執行 AI 偵測
        print("🔍 正在進行偵測...")
        
        result = model.predict(filepath, confidence=40, overlap=30)
        
        predictions = result.json()['predictions']
        
        print(f"✅ 偵測完成，找到 {len(predictions)} 個物件") 
        
        # 統計偵測結果（按類別分組）
        class_stats = {}
        
        # 遍歷每個偵測結果
        for pred in predictions:
            # 取得類別名稱（例如：'RBC'）
            class_name = pred['class']
            
            # 取得信心度（轉換成百分比：0.87 → 87）
            confidence = pred['confidence'] * 100
            
            # 如果這個類別第一次出現，初始化統計資料
            if class_name not in class_stats:
                class_stats[class_name] = {
                    'count': 0,           # 該類別出現次數
                    'confidences': []     # 該類別所有偵測的信心度列表
                }
            
            # 累加該類別的數量
            class_stats[class_name]['count'] += 1
            
            # 記錄該次偵測的信心度
            class_stats[class_name]['confidences'].append(confidence)
        
        
        # 計算每個類別的平均信心度
        for class_name in class_stats:
            # 取得該類別的所有信心度
            confidences = class_stats[class_name]['confidences']
            
            # 計算平均值
            avg_confidence = sum(confidences) / len(confidences)
            
            # 將平均信心度加入統計資料
            class_stats[class_name]['avg_confidence'] = avg_confidence
        
        # 刪除臨時檔案（釋放硬碟空間）
        if os.path.exists(filepath):
            # 刪除暫存圖片
            os.remove(filepath)
        
        # 返回偵測結果給前端
        return jsonify({
            'success': True,                    # 偵測成功
            
            # 統計資料（給右側進度條用）
            'predictions': class_stats,
            
            # 完整偵測結果（給 Canvas 繪製偵測框用）
            'detections': predictions,
            
            # 總共偵測到幾個物件
            'total_detected': len(predictions)
        })
        
    # 例外處理：捕捉所有執行時錯誤
    except Exception as e:
        # 在終端機顯示錯誤資訊
        print(f"❌ 偵測錯誤: {e}")
        print(f"錯誤類型: {type(e).__name__}")
        
        # 印出完整的錯誤追蹤（Stack Trace）
        import traceback
        traceback.print_exc()
        
        # 返回錯誤訊息給前端
        return jsonify({
            'success': False,      # 偵測失敗
            'error': str(e)        # 錯誤訊息
        })

# 主程式入口：啟動 Flask 伺服器
if __name__ == '__main__':
    # 顯示系統初始化狀態
    print("\n" + "=" * 60)
    
    if model is not None:
        # 模型載入成功
        print("✅ ✅ ✅ 系統初始化完成！✅ ✅ ✅")
        
    else:
        # 模型載入失敗（但伺服器仍可啟動）
        print("⚠️  ⚠️  ⚠️  系統啟動但模型未載入 ⚠️  ⚠️  ⚠️")
        print(f"錯誤: {model_error}")
    
    print("=" * 60)
    print("🚀 伺服器啟動中...")
    print("📱 請在瀏覽器開啟: http://127.0.0.1:5000")
    
    # Windows 使用提示
    print("\n💡 使用提示：")
    print("   - 瀏覽器會請求攝像頭權限，請點選「允許」")
    print("   - 攝像頭畫面會直接顯示在網頁上")
    print("   - 系統每 2 秒自動偵測一次")
    
    
    # 如果模型未載入，顯示警告訊息
    if model is None:
        print("\n⚠️  警告：Roboflow 模型未成功載入")
        print("   請檢查上方的錯誤訊息")
    
    print("=" * 60 + "\n")
    
    # 啟動 Flask 開發伺服器
    app.run(
    
        debug=False,
        threaded=True,
        port=5000
    )


