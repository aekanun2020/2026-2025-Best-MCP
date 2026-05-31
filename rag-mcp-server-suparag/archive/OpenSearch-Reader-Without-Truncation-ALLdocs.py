from opensearchpy import OpenSearch

def connect_to_opensearch(host="localhost", port=9200, use_ssl=False):
    """เชื่อมต่อกับ OpenSearch"""
    opensearch_client = OpenSearch(
        hosts=[{'host': host, 'port': port}],
        use_ssl=use_ssl
    )
    return opensearch_client

def get_all_documents_with_context(client, index_name):
    """ดึงเอกสารทั้งหมดที่มี contextualized_content"""
    query = {
        "query": {
            "exists": {
                "field": "contextualized_content"
            }
        },
        "size": 1000  # จำนวนสูงสุดที่จะแสดง (ปรับตามต้องการ)
    }
    
    response = client.search(
        index=index_name,
        body=query
    )
    
    return response["hits"]["hits"]

def display_all_documents_with_context(host="localhost", port=9200, index_name="rag-contextual"):
    """แสดงข้อมูลของเอกสารทั้งหมดที่มี contextualized_content"""
    client = connect_to_opensearch(host, port)
    
    # ดึงเอกสารทั้งหมด
    docs = get_all_documents_with_context(client, index_name)
    
    print(f"พบ {len(docs)} เอกสารที่มี contextualized_content\n")
    
    # แสดงข้อมูลของแต่ละเอกสาร
    for i, doc in enumerate(docs):
        source = doc["_source"]
        
        print(f"=== เอกสาร {i+1}/{len(docs)} ===")
        
        # แสดงข้อมูลพื้นฐาน
        print(f"ID: {doc['_id']}")
        
        if "title" in source:
            print(f"\nTitle: {source['title']}")
        
        # แสดง content และ contextualized_content
        if "content" in source:
            print("\n--- CONTENT ---")
            print(source["content"])
        
        if "contextualized_content" in source:
            print("\n--- CONTEXTUALIZED CONTENT ---")
            print(source["contextualized_content"])
        
        # แสดง metadata
        if "metadata" in source:
            print("\n--- METADATA ---")
            metadata = source["metadata"]
            if "summary" in metadata:
                print(f"Summary: {metadata['summary']}")
            if "questions" in metadata:
                print("Related Questions:")
                for q in metadata.get("questions", []):
                    print(f"- {q}")
            if "entities" in metadata:
                entities = metadata.get("entities", [])
                if isinstance(entities, list):
                    print(f"Entities: {', '.join(entities)}")
                else:
                    print(f"Entities: {entities}")
            if "source" in metadata:
                print(f"Source: {metadata['source']}")
        
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    # แก้ไข host และ port ตามสภาพแวดล้อมของคุณ
    HOST = "34.41.37.53"  # หรือ "localhost"
    PORT = 9200
    INDEX_NAME = "rag-contextual"
    
    # แสดงเอกสารทั้งหมดที่มี contextualized_content
    display_all_documents_with_context(HOST, PORT, INDEX_NAME)
