
export function RenderImage({ imgSrc, altText = "Image" }) {
    return <img src={imgSrc} alt={altText} />;
}