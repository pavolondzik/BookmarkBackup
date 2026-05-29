import {
  useCallback,
  useLayoutEffect,
  useRef,
  type TextareaHTMLAttributes,
} from "react";

type Props = Omit<
  TextareaHTMLAttributes<HTMLTextAreaElement>,
  "rows" | "style"
> & {
  value: string;
};

function syncHeight(el: HTMLTextAreaElement) {
  el.style.height = "auto";
  el.style.height = `${el.scrollHeight}px`;
}

export function AutoResizeTextarea({
  value,
  onChange,
  className,
  ...rest
}: Props) {
  const ref = useRef<HTMLTextAreaElement>(null);

  const resize = useCallback(() => {
    const el = ref.current;
    if (el) syncHeight(el);
  }, []);

  useLayoutEffect(() => {
    resize();
  }, [value, resize]);

  return (
    <textarea
      ref={ref}
      rows={1}
      value={value}
      onChange={(event) => {
        onChange?.(event);
        syncHeight(event.currentTarget);
      }}
      className={className}
      style={{ overflow: "hidden", resize: "none" }}
      {...rest}
    />
  );
}
