import { photoUrl, type Photo } from "@/lib/photos";

/** A Commons photo, hosted on the site and "taped" onto the page, with the credit its licence requires. */
export function CarPhoto({ photo, alt }: { photo: Photo; alt: string }) {
  const filePage = `https://commons.wikimedia.org/wiki/File:${encodeURIComponent(photo.file.replace(/ /g, "_"))}`;
  return (
    <figure className="photo">
      {/* Hosted here (public/cars), copied from Wikimedia Commons with its credit below. */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={photoUrl(photo, 360)}
        srcSet={`${photoUrl(photo, 360)} 360w, ${photoUrl(photo, 960)} 960w`}
        sizes="(max-width: 820px) 90vw, 520px"
        alt={alt}
        decoding="async"
      />
      <figcaption>
        Photo: <a href={filePage} target="_blank" rel="noreferrer">{photo.author}</a>
        {" · "}
        {photo.licenseUrl ? (
          <a href={photo.licenseUrl} target="_blank" rel="noreferrer">{photo.license}</a>
        ) : (
          photo.license
        )}
      </figcaption>
    </figure>
  );
}
