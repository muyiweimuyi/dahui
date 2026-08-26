import json
import os

DATA_FILE = "contacts.json"

def load_data():
    """从 JSON 文件加载数据，如果文件不存在返回空字典"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    """保存字典到 JSON 文件"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print("数据已保存。")

def add_contact(contacts):
    """添加新联系人"""
    name = input("请输入姓名: ").strip()
    if not name:
        print("姓名不能为空！")
        return
    if name in contacts:
        print(f"联系人 {name} 已存在，将覆盖。")
    age = input("请输入年龄: ").strip()
    city = input("请输入城市: ").strip()
    contacts[name] = {"age": age, "city": city}
    print(f"已添加/更新联系人 {name}")

def show_contacts(contacts):
    """显示所有联系人"""
    if not contacts:
        print("暂无联系人。")
        return
    print("\n--- 通讯录 ---")
    for name, info in contacts.items():
        print(f"{name}: 年龄 {info.get('age', '未知')}, 城市 {info.get('city', '未知')}")
    print("---------------\n")

def main():
    contacts = load_data()
    print("欢迎使用通讯录管理程序！")
    while True:
        print("\n请选择操作:")
        print("1. 添加/更新联系人")
        print("2. 查看所有联系人")
        print("3. 保存数据到文件")
        print("4. 从文件重新加载数据（将覆盖当前内存数据）")
        print("5. 退出程序")
        choice = input("请输入数字 (1-5): ").strip()
        if choice == "1":
            add_contact(contacts)
        elif choice == "2":
            show_contacts(contacts)
        elif choice == "3":
            save_data(contacts)
        elif choice == "4":
            contacts = load_data()
            print("数据已重新加载。")
        elif choice == "5":
            # 退出前询问是否保存
            save_choice = input("是否保存当前数据？(y/n): ").strip().lower()
            if save_choice == 'y':
                save_data(contacts)
            print("再见！")
            break
        else:
            print("无效输入，请输入 1-5。")

if __name__ == "__main__":
    main()
