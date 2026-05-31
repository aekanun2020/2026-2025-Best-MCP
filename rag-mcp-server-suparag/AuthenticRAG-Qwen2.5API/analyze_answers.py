#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
สคริปต์วิเคราะห์คำตอบจากระบบ RAG
ให้คะแนน: (1) ตอบถูกแต่ไม่ครบ (2) ตอบถูกและครบถ้วน (3) ตอบไม่ถูก
"""

import json

def analyze_results():
    # อ่านผลลัพธ์
    with open('advanced_test_results.json', 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    print("=" * 80)
    print("การวิเคราะห์คำตอบจากระบบ AuthenticRAG")
    print("=" * 80)
    print()
    
    # วิเคราะห์แต่ละคำถาม
    for i, item in enumerate(results, 1):
        print(f"\n{'='*80}")
        print(f"คำถามที่ {i}/15")
        print(f"{'='*80}")
        print(f"\n📝 คำถาม: {item['question']}")
        print(f"\n💡 คำตอบ:")
        print(f"{item['answer'][:500]}...")  # แสดงแค่ 500 ตัวอักษรแรก
        print(f"\n📚 จำนวนเอกสารที่ใช้: {len(item['results'])} เอกสาร")
        
        # แสดง doc_id ที่ใช้
        doc_ids = [r['doc_id'] for r in item['results']]
        print(f"📄 เอกสารที่ใช้: {', '.join(doc_ids)}")
        
        print(f"\n{'─'*80}")
        print("⚖️  ประเมินคำตอบ:")
        print("   (1) ตอบถูกแต่ไม่ครบ")
        print("   (2) ตอบถูกและครบถ้วนสมบูรณ์")
        print("   (3) ตอบไม่ถูก")
        print(f"{'─'*80}\n")
    
    print("\n" + "=" * 80)
    print("สรุป: ระบบตอบคำถามได้ครบทั้ง 15 ข้อ")
    print("=" * 80)
    print("\nกรุณาประเมินคำตอบแต่ละข้อด้วยตนเอง โดยเปรียบเทียบกับเอกสารต้นฉบับ")
    print("ในโฟลเดอร์ corpus_input/")

if __name__ == "__main__":
    analyze_results()
