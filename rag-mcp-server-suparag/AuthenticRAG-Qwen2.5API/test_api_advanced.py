#!/usr/bin/env python3
"""
Test advanced questions through the new API
ทดสอบคำถามที่ท้าทายผ่าน API ใหม่
"""

import requests
import json
import time
from datetime import datetime

API_BASE_URL = "http://localhost:8001"

# ชุดคำถามที่ท้าทาย (เหมือนกับ test_advanced_questions.py)
questions = [
    # 1. คำถามเปรียบเทียบข้ามโรค
    "เปรียบเทียบระยะฟักตัวของโรคหัดเยอรมันกับอหิวาตกโรค แล้วอธิบายว่าทำไมถึงต่างกัน",
    
    # 2. คำถามเชิงลึกเกี่ยวกับกลไก
    "อธิบายกลไกที่ทำให้ผู้ป่วยอหิวาตกโรคไม่มีไข้ แต่ผู้ป่วยหัดเยอรมันกลับมีไข้",
    
    # 3. คำถามเกี่ยวกับภาวะแทรกซ้อนที่หายาก
    "ภาวะ Forchheimer spots ในโรคหัดเยอรมันคืออะไร และพบได้บ่อยแค่ไหน",
    
    # 4. คำถามเชิงตัวเลขและสถิติ
    "ในปี 2010 มีผู้เสียชีวิตจากอหิวาตกโรคทั่วโลกประมาณเท่าไหร่ และในประเทศไทยปี 2555 พบอัตราการเกิดโรคเท่าไหร่",
    
    # 5. คำถามเกี่ยวกับการรักษาเฉพาะกลุ่ม
    "หญิงตั้งครรภ์ที่เป็นหัดเยอรมันในเดือนที่ 2 ควรได้รับการรักษาอย่างไร และมีทางเลือกอะไรบ้าง",
    
    # 6. คำถามเชิงเหตุผล
    "ทำไมต้อกระจกที่เกิดจากการบาดเจ็บจึงอาจเกิดขึ้นได้ภายใน 2-3 ปีหลังอุบัติเหตุ แม้จะรักษาถูกต้องแล้วก็ตาม",
    
    # 7. คำถามเกี่ยวกับการป้องกันเฉพาะกลุ่ม
    "ผู้ที่ทำงานเกี่ยวกับการเชื่อมโลหะควรป้องกันต้อกระจกอย่างไร และทำไม",
    
    # 8. คำถามเชิงซับซ้อนข้ามหัวข้อ
    "เปรียบเทียบวิธีการวินิจฉัยโรคหัดเยอรมันในผู้ใหญ่กับการวินิจฉัยในทารกที่เกิดจากมารดาติดเชื้อ",
    
    # 9. คำถามเกี่ยวกับยาและการรักษา
    "ยา Tetracycline ใช้รักษาอหิวาตกโรคในขนาดเท่าไหร่ และใช้นานแค่ไหน สำหรับเด็กและหญิงตั้งครรภ์ควรใช้ยาอะไรแทน",
    
    # 10. คำถามเชิงวิเคราะห์
    "วิเคราะห์ว่าทำไมโรคกรดไหลย้อนจึงพบได้บ่อยในผู้สูงอายุมากกว่าคนหนุ่มสาว",
    
    # 11. คำถามเกี่ยวกับความแตกต่างของเทคนิค
    "เปรียบเทียบวิธีผ่าตัดต้อกระจกแบบ Phacoemulsification กับวิธีผ่าตัดแบบเก่า มีข้อดีข้อเสียอย่างไร",
    
    # 12. คำถามเกี่ยวกับปัจจัยเสี่ยงที่ซับซ้อน
    "อธิบายความสัมพันธ์ระหว่างโรคเบาหวานกับโรคกรดไหลย้อน และทำไมผู้ป่วยเบาหวานจึงมีความเสี่ยงสูง",
    
    # 13. คำถามเกี่ยวกับชื่อทางการแพทย์
    "Congenital Rubella Syndrome (CRS) มีอาการหลักอะไรบ้าง และเกิดขึ้นได้อย่างไร",
    
    # 14. คำถามเชิงเปรียบเทียบการรักษา
    "เปรียบเทียบการรักษาอหิวาตกโรคในผู้ป่วยที่มีอาการเล็กน้อยกับผู้ป่วยที่มีอาการรุนแรง",
    
    # 15. คำถามเกี่ยวกับภาวะพิเศษ
    "ทารกที่เกิดมาพร้อมต้อกระจกจากมารดาที่เป็นหัดเยอรมันควรได้รับการผ่าตัดเมื่ออายุเท่าไหร่ และทำไม"
]

def test_api_health():
    """ตรวจสอบสถานะ API"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ API Status: Healthy")
            print(f"   - OpenSearch: {'Connected' if data['opensearch_connected'] else 'Disconnected'}")
            print(f"   - Model: {'Loaded' if data['model_loaded'] else 'Not Loaded'}")
            print(f"   - Documents: {data['documents_indexed']}")
            return True
        else:
            print("❌ API Status: Unhealthy")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return False

def ask_question(query, top_k=10, final_top_k=5):
    """ถามคำถามผ่าน API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/answer",
            json={
                "query": query,
                "top_k": top_k,
                "final_top_k": final_top_k
            },
            timeout=60
        )
        
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, {"error": f"API Error: {response.status_code}"}
    except Exception as e:
        return False, {"error": str(e)}

def main():
    print("=" * 80)
    print("🧪 Advanced Test Questions through API")
    print("=" * 80)
    print()
    
    # Check API health
    if not test_api_health():
        print("\n❌ API is not available. Please start the API server first.")
        print("   Run: python api_server.py")
        return
    
    print()
    print("=" * 80)
    print(f"จำนวนคำถามทั้งหมด: {len(questions)} ข้อ")
    print("=" * 80)
    print()
    
    results = []
    total_time = 0
    
    for i, question in enumerate(questions, 1):
        print(f"\n{'='*80}")
        print(f"คำถามที่ {i}/{len(questions)}")
        print(f"{'='*80}")
        print(f"❓ {question}")
        print()
        
        start_time = time.time()
        success, result = ask_question(question)
        elapsed_time = time.time() - start_time
        
        if success:
            print(f"✅ คำตอบ:")
            print(f"{result['answer']}")
            print()
            print(f"⏱️  เวลาที่ใช้: {result['generation_time']:.2f} วินาที")
            print(f"📚 เอกสารที่ใช้: {len(result['sources'])} เอกสาร")
            
            results.append({
                "question": question,
                "answer": result['answer'],
                "sources": result['sources'],
                "generation_time": result['generation_time']
            })
            
            total_time += result['generation_time']
        else:
            print(f"❌ เกิดข้อผิดพลาด: {result.get('error', 'Unknown error')}")
            results.append({
                "question": question,
                "answer": f"Error: {result.get('error', 'Unknown error')}",
                "sources": [],
                "generation_time": 0
            })
    
    # Save results
    output_file = "api_advanced_test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "test_date": datetime.now().isoformat(),
            "total_questions": len(questions),
            "total_time": total_time,
            "average_time": total_time / len(questions) if questions else 0,
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    print()
    print("=" * 80)
    print("✅ การทดสอบเสร็จสมบูรณ์!")
    print("=" * 80)
    print()
    print(f"📊 สรุปผลการทดสอบ:")
    print(f"   - จำนวนคำถามทั้งหมด: {len(questions)} ข้อ")
    print(f"   - เวลารวมทั้งหมด: {total_time:.2f} วินาที")
    print(f"   - เวลาเฉลี่ยต่อคำถาม: {total_time/len(questions):.2f} วินาที")
    print()
    print(f"📁 ผลลัพธ์ถูกบันทึกที่: {output_file}")
    print()

if __name__ == "__main__":
    main()
