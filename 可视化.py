import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from sqlalchemy import create_engine

PASSWORD = "root123"
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

# 连接 MySQL
engine = create_engine(f"mysql+pymysql://root:{PASSWORD}@localhost:3306/ecommerce_analysis")

print("正在读取数据...")

# === 1. 漏斗数据：各行为类型的独立用户数 ===
funnel = pd.read_sql("""
    SELECT
        behavior_type,
        COUNT(DISTINCT user_id) AS users
    FROM user_behaviors
    GROUP BY behavior_type
    ORDER BY FIELD(behavior_type, 'pv', 'fav', 'cart', 'buy')
""", engine)
print(funnel)

# === 2. 类目销量 Top 10 ===
top_categories = pd.read_sql("""
    SELECT
        category_id,
        COUNT(*) AS sales
    FROM user_behaviors
    WHERE behavior_type = 'buy'
    GROUP BY category_id
    ORDER BY sales DESC
    LIMIT 10
""", engine)
print(top_categories)

# === 3. 用户分层数据 ===
user_levels = pd.read_sql("""
    WITH user_level AS (
        SELECT
            user_id,
            CASE
                WHEN COUNT(*) >= 5 THEN '高活跃'
                WHEN COUNT(*) >= 2 THEN '中活跃'
                ELSE '低活跃'
            END AS 用户层级
        FROM user_behaviors
        WHERE behavior_type = 'buy'
        GROUP BY user_id
    )
    SELECT
        用户层级,
        COUNT(*) AS 用户数
    FROM user_level
    GROUP BY 用户层级
    ORDER BY 用户数 DESC
""", engine)
print(user_levels)

# === 4. 购买时段分布 ===
hourly = pd.read_sql("""
    SELECT
        HOUR(FROM_UNIXTIME(timestamp)) AS hour,
        COUNT(*) AS purchases
    FROM user_behaviors
    WHERE behavior_type = 'buy'
    GROUP BY HOUR(FROM_UNIXTIME(timestamp))
    ORDER BY hour
""", engine)
print(hourly)

print("数据读取完成，开始绘图...\n")


# 转化漏斗图
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('电商用户行为数据分析', fontsize=18, fontweight='bold', y=1.02)

# 漏斗数据
stages = ['浏览\n(pv)', '收藏\n(fav)', '加购\n(cart)', '购买\n(buy)']
users = funnel['users'].values.tolist()

# 计算转化率标签
rates = []
for i in range(len(users)):
    if i == 0:
        rates.append(f"{users[i]:,} 人\n100%")
    else:
        pct = users[i] / users[0] * 100
        rates.append(f"{users[i]:,} 人\n{pct:.2f}%")

# 画漏斗（用条形图模拟）
colors = ['#2c7da0', '#3a9bb8', '#52b5cf', '#7acce0']
ax1 = axes[0, 0]
bars = ax1.barh(stages, users, color=colors, height=0.6)

# 在条形上标注数值
for bar, label in zip(bars, rates):
    ax1.text(bar.get_width() + 2000, bar.get_y() + bar.get_height()/2, label,
             va='center', fontsize=10, fontweight='bold', color='#1a5d76')

ax1.set_xlabel('用户数', fontsize=10)
ax1.set_title('用户行为转化漏斗', fontsize=13, fontweight='bold', color='#0b3b4f')
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)

# 类目销量 Top 10 柱状图

ax2 = axes[0, 1]
categories = [f"类目{c}" for c in top_categories['category_id'].astype(str)]
sales = top_categories['sales'].values

bars2 = ax2.bar(categories, sales, color='#2c7da0', edgecolor='white', linewidth=0.5)
for bar in bars2:
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, str(int(bar.get_height())),
             ha='center', fontsize=9, fontweight='bold', color='#1a5d76')

ax2.set_title('类目销量 Top 10', fontsize=13, fontweight='bold', color='#0b3b4f')
ax2.set_ylabel('销量', fontsize=10)
ax2.tick_params(axis='x', rotation=30)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)

# 图3：用户分层饼图
ax3 = axes[1, 0]
labels = user_levels['用户层级'].tolist()
sizes = user_levels['用户数'].tolist()
pie_colors = ['#e88d8d', '#f0c27a', '#7acce0']
# 动态生成 explode
explode = tuple(0.1 if i == len(sizes)-1 else 0.05 for i in range(len(sizes)))

wedges, texts, autotexts = ax3.pie(
    sizes, labels=labels, autopct='%1.2f%%',
    colors=pie_colors, explode=explode,
    startangle=90, textprops={'fontsize': 11}
)
for at in autotexts:
    at.set_fontweight('bold')
ax3.set_title('用户购买频次分层', fontsize=13, fontweight='bold', color='#0b3b4f')

# 添加人数标注
legend_labels = [f"{l}: {s:,}人" for l, s in zip(labels, sizes)]
ax3.legend(legend_labels, loc='lower right', fontsize=8)

# 购买时段分布折线图
ax4 = axes[1, 1]
hours_range = range(0, 10)  #
hour_vals = []
for h in hours_range:
    match = hourly[hourly['hour'] == h]
    hour_vals.append(match['purchases'].values[0] if not match.empty else 0)

ax4.plot(list(hours_range), hour_vals, marker='o', color='#2c7da0',
         linewidth=2.5, markersize=8, markerfacecolor='white',
         markeredgewidth=2, markeredgecolor='#2c7da0')

# 在点上标数值
for x, y in zip(hours_range, hour_vals):
    ax4.text(x, y + 150, str(int(y)), ha='center', fontsize=9,
             fontweight='bold', color='#1a5d76')

ax4.set_xlabel('小时', fontsize=10)
ax4.set_ylabel('购买次数', fontsize=10)
ax4.set_title('购买时段分布', fontsize=13, fontweight='bold', color='#0b3b4f')
ax4.set_xticks(list(hours_range))
ax4.grid(True, alpha=0.2, linestyle='--')
ax4.spines['top'].set_visible(False)
ax4.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig('电商用户行为分析图表.png', dpi=200, bbox_inches='tight')
print("[完成] 图表已保存到: 电商用户行为分析图表.png")
plt.show()
