from pathlib import Path

from zebrafish_tracking.io.mastodon_csv import read_mastodon_links, read_mastodon_spots


def test_pixel_and_micrometre_coordinate_conversion(tmp_path: Path):
    spots = tmp_path / "spots.csv"
    spots.write_text(
        "spot_id,frame,track_id,x_px,y_px,z_slice,x_um,y_um,z_um,reviewed\n"
        "1,0,7,20,40,5,6.94,13.88,3.5,1\n"
        "2,1,7,22,42,6,7.634,14.574,4.2,0\n",
        encoding="utf-8",
    )

    pixel = read_mastodon_spots(
        spots,
        coordinate_mode="pixels",
        frame_offset=1,
        first_mastodon_frame=0,
        last_mastodon_frame=1,
        xy_downsample=2,
    )
    assert (pixel[0].frame, pixel[0].x, pixel[0].y, pixel[0].z) == (1, 10, 20, 5)

    physical = read_mastodon_spots(
        spots,
        coordinate_mode="micrometres",
        frame_offset=1,
        first_mastodon_frame=0,
        last_mastodon_frame=1,
        xy_downsample=2,
        xy_pixel_size_um=0.347,
        z_spacing_um=0.7,
        reviewed_only=True,
    )
    assert len(physical) == 1
    assert round(physical[0].x, 10) == 10
    assert round(physical[0].y, 10) == 20
    assert round(physical[0].z, 10) == 5


def test_reviewed_link_filter(tmp_path: Path):
    links = tmp_path / "links.csv"
    links.write_text(
        "source_spot_id,target_spot_id,reviewed\n1,2,1\n2,3,0\n",
        encoding="utf-8",
    )
    assert len(read_mastodon_links(links, reviewed_only=True)) == 1
