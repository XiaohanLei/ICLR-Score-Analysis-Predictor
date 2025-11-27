import openreview

import pandas as pd

from tqdm import tqdm



def get_iclr_data(year="2024"):

    print(f"🚀 开始爬取 ICLR {year} 数据 (修复版)...")

   

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



    for i, note in enumerate(tqdm(submissions)):

        paper_id = note.id

        title = note.content.get('title', {}).get('value', 'Unknown Title')

       

        replies = note.details.get('directReplies', [])

       

        decision = "Pending"

        scores = []

       

        # --- 遍历回复寻找 Decision 和 Reviews ---

        for reply in replies:

            # 获取该回复的所有 invitation 标签

            invitations = reply.get('invitations', [])

           

            # 将 list 转为字符串方便查找，或者遍历查找

            # 关键修复：不再匹配死板的 ID，而是匹配关键词

            is_decision = False

            is_review = False

           

            for inv in invitations:

                # 排除 Meta Review, Desk Reject 等干扰项，只找 Decision

                if 'Decision' in inv and 'Desk_Reject' not in inv and 'Withdrawn' not in inv:

                    is_decision = True

                # 找 Official Review

                if 'Official_Review' in inv:

                    is_review = True



            # --- 提取 Decision ---

            if is_decision:

                try:

                    # OpenReview V2 结构通常是 content -> decision -> value

                    decision_val = reply['content']['decision']['value']

                    decision = decision_val

                    debug_decision_count += 1

                except KeyError:

                    # 有时候结构可能是直接 content -> decision

                    pass



            # --- 提取分数 (Scores) ---

            if is_review:

                try:

                    # ICLR 2024 分数格式通常在 rating -> value 中

                    # 例如: "8: Strong Accept"

                    rating_obj = reply['content'].get('rating', {})

                    rating_str = rating_obj.get('value', '')

                   

                    if rating_str:

                        # 提取冒号前的数字

                        score = int(rating_str.split(':')[0])

                        scores.append(score)

                        debug_review_count += 1

                except Exception:

                    pass

       

        # 如果没有 Decision (可能是撤稿或尚未出结果)，跳过

        if decision == "Pending":

            continue



        # 简化状态

        status = "Accept" if "Accept" in decision else "Reject"

       

        # 只有当有分数时才记录 (没有分数的可能是 Desk Reject)

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

        print("❌ 错误: 仍然没有提取到有效数据。可能是 API 结构与预期完全不符。")

        # 打印第一篇的数据结构供调试

        if len(submissions) > 0:

            print("\n🔍 第一篇论文的回复 ID 示例 (用于排查):")

            first_replies = submissions[0].details.get('directReplies', [])

            for r in first_replies:

                print(f"  - Invitation: {r.get('invitations')}")

        return pd.DataFrame() # 返回空表防止报错



    # 3. 转换为 DataFrame 并保存

    df = pd.DataFrame(data)

    filename = f'iclr_{year}_real_data.csv'

    df.to_csv(filename, index=False)

   

    print(f"\n🎉 爬取完成！数据已保存至 {filename}")

    print(f"共处理有效论文: {len(df)} 篇")

    print(f"Accept 数量: {len(df[df['status'] == 'Accept'])}")

    print(f"Reject 数量: {len(df[df['status'] == 'Reject'])}")

   

    return df



if __name__ == "__main__":

    df = get_iclr_data("2024")