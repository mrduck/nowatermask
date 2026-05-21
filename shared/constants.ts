export const SITE = {
  name: "免费去水印工具",
  description: "AI鉴图+双模式去水印工具，支持证件照、写真照、AI生成照片快速去水印，完全免费",
  url: "https://watermark-removal.example.com",
  toolSlug: "ai-watermark-removal"
} as const

export const FEATURES = [
  { id: "auto", name: "自动模式", desc: "AI智能检测水印，一键去除" },
  { id: "manual", name: "手动精修", desc: "涂抹水印区域，精准消除" }
] as const