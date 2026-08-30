import pandas as pd
df = pd.read_csv(r'C:\Users\mahes\Downloads\attack model\data\archive_combined.csv')
s = df.sample(n=50000, random_state=42)
# Create multiple source IP groups for train/val/test splitting
s['src_ip'] = ['10.0.' + str(i//5000) + '.1' for i in range(len(s))]
s['dst_ip'] = '10.0.0.254'
s.to_csv(r'C:\Users\mahes\Downloads\attack model\data\archive_combined.csv', index=False)
print(f"OK: {len(s)} rows, {s['src_ip'].nunique()} groups, labels: {s['label'].value_counts().to_dict()}")
