type Props = {
  size?: "small" | "big";
  float?: boolean;
  /** 深色背景下使用（聊天室），自动切换为亮色轮廓 */
  dark?: boolean;
};

export default function Mascot({ size, float, dark: _dark }: Props) {
  const classes = ["mascot", size, float ? "float" : ""].filter(Boolean).join(" ");
  return (
    <div className={classes} aria-hidden>
      <img src="/favicon.svg" alt="" />
    </div>
  );
}
