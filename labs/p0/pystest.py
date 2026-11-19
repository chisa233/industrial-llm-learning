import sys

print("Python 环境：", sys.executable)

temperatures = [42, 51, 68, 75]
threshold = 60

for temp in temperatures:
    if temp > threshold:
        print(f"温度异常：{temp}℃")
    else:
        print(f"温度正常：{temp}℃")