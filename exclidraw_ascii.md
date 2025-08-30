
## 目标
将exclidraw.json 中的图形转换为ascii字符图形


例如：
将一个矩形对象转换为ascii矩形：
```
{
  "type": "rectangle",
  "x": 0,
  "y": 0,
  "width": 10,
  "height": 10
}
```

====>

+-------------+
|             |
+-------------+



## 实现方式

用python实现

## 使用方法

```
python exclidraw2ascii.py exclidraw.json
```

### 需要支持的对象

1. 矩形
2. 圆形/椭圆
3. 菱形
4. 有向线段
5. 无向线段
6. 弧线线段

### 无需关心的

1. 边框颜色
2. 填充颜色
