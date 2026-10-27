import type { Photo } from "@/lib/photos";

/** A Commons photo "taped" onto the page, with the credit its licence requires. */
export function CarPhoto({ photo, alt }: { photo: Photo; alt: string }) {
  const filePage = `https://commons.wikimedia.org/wiki/File:${encodeURIComponent(photo.file.replace(/ /g, "_"))}`;
  return (
    <figure className="photo">
      {/* Hotlinked from Wikimedia, which serves its own resized thumbnails. */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={photo.src} alt={alt} loading="lazy" decoding="async" />
      <figcaption>
        Photo: <a href={filePage} target="_blank" rel="noreferrer">{photo.author}</a>
        {" · "}
        {photo.licenseUrl ? (
          <a href={photo.licenseUrl} target="_blank" rel="noreferrer">{photo.license}</a>
        ) : (
          photo.license
        )}
        {photo.note && <> · {photo.note}</>}
      </figcaption>
    </figure>
  );
}
