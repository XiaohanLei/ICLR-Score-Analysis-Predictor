import openreview
import pandas as pd
from tqdm import tqdm

def get_iclr_data(year="2025"):
    print(f"🚀 开始爬取 ICLR {year} 数据 (V3 鲁棒版)...")
    
    client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')
    venue_id = f'ICLR.cc/{year}/Conference'
    submission_invitation = f'{venue_id}/-/Submission'
    
    print("📥 正在获取所有投稿列表...")
    submissions = client.get_all_notes(invitation=submission_invitation, details='directReplies')
    print(f"✅ 获取到 {len(submissions)} 篇投稿。开始解析...")

    data = []
    
    # 调试计数器
    debug_decision_count = 0
    debug_review_count = 0
    debug_structure_printed = False # 确保只打印一次结构

    for i, note in enumerate(tqdm(submissions)):
        paper_id = note.id
        title = note.content.get('title', {}).get('value', 'Unknown Title')
        
        replies = note.details.get('directReplies', [])
        
        decision = "Pending"
        scores = []
        
        for reply in replies:
            invitations = reply.get('invitations', [])
            
            # --- 1. 寻找 Decision ---
            is_decision = False
            for inv in invitations:
                if 'Decision' in inv and 'Desk_Reject' not in inv and 'Withdrawn' not in inv:
                    is_decision = True
                    break
            
            if is_decision:
                try:
                    # 尝试获取 decision value
                    decision_val = reply['content']['decision']['value']
                    decision = decision_val
                    debug_decision_count += 1
                except Exception:
                    pass

            # --- 2. 寻找 Official Review (分数) ---
            is_review = False
            for inv in invitations:
                if 'Official_Review' in inv:
                    is_review = True
                    break
            
            if is_review:
                # 获取 content 字典
                content = reply.get('content', {})
                
                # --- 核心修复：更鲁棒的分数提取逻辑 ---
                score_val = None
                
                # 尝试不同的键名 (ICLR 通常是 rating，但也可能是 recommendation)
                if 'rating' in content:
                    score_val = content['rating'].get('value')
                elif 'recommendation' in content:
                    score_val = content['recommendation'].get('value')
                
                # 如果这是第一次遇到 Review 且还没提取到分数，打印结构供调试
                if not debug_structure_printed and score_val is None:
                    print(f"\n🔍 [DEBUG] 第一篇 Review 的 Content 结构: {content.keys()}")
                    if 'rating' in content:
                        print(f"   rating value type: {type(content['rating'].get('value'))}")
                        print(f"   rating value: {content['rating'].get('value')}")
                    debug_structure_printed = True

                if score_val is not None:
                    try:
                        # 核心修复：无论它是 int 还是 str，先转为 str
                        score_str = str(score_val) 
                        
                        # 如果是 "8: Strong Accept"，取冒号前
                        # 如果是 "8"，split(':') 后还是 "8"
                        score_clean = score_str.split(':')[0].strip()
                        
                        scores.append(int(score_clean))
                        debug_review_count += 1
                    except Exception as e:
                        # 只有在转换 int 失败时才忽略
                        # print(f"解析分数失败: {score_val} -> {e}") 
                        pass

        # 如果没有 Decision (可能是撤稿或尚未出结果)，跳过
        if decision == "Pending":
            continue

        status = "Accept" if "Accept" in decision else "Reject"
        
        if scores:
            data.append({
                "id": paper_id,
                "title": title,
                "year": int(year),
                "scores": scores,
                "mean_score": round(sum(scores) / len(scores), 2),
                "status": status,
                "raw_decision": decision
            })

    print(f"\n📊 调试信息:")
    print(f"  - 找到 Decision 的次数: {debug_decision_count}")
    print(f"  - 找到 Review 分数的次数: {debug_review_count}")
    
    if len(data) == 0:
        print("❌ 错误: 仍然没有提取到数据。请查看上方 DEBUG 输出的结构。")
        return pd.DataFrame()

    # 保存
    df = pd.DataFrame(data)
    filename = f'iclr_{year}_real_data.csv'
    df.to_csv(filename, index=False)
    
    print(f"\n🎉 爬取完成！数据已保存至 {filename}")
    print(f"共处理有效论文: {len(df)} 篇")
    
    return df

if __name__ == "__main__":
    df = get_iclr_data("2025")