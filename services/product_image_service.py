"""Images locales validées ; aucun chemin provenant du navigateur n'est utilisé."""
from io import BytesIO
from pathlib import Path
from uuid import uuid4
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError
from config import DATA_DIR
from models.product import Product

MAX_BYTES = 5 * 1024 * 1024
MAX_PIXELS = 12_000_000


class ProductImageService:
    def __init__(self, db, image_dir=None):
        self.db = db
        self.image_dir = Path(image_dir) if image_dir is not None else DATA_DIR / 'Images'

    def save(self, product_id, content):
        product = self.db.get(Product, product_id)
        if not product:
            raise ValueError('Produit introuvable.')
        if not isinstance(content, bytes) or not content or len(content) > MAX_BYTES:
            raise ValueError('L’image doit contenir au maximum 5 Mo.')
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                with Image.open(BytesIO(content)) as source:
                    if source.format not in ('JPEG', 'PNG'):
                        raise ValueError('Seules les images JPEG et PNG sont acceptées.')
                    if source.width * source.height > MAX_PIXELS:
                        raise ValueError('L’image est trop grande.')
                    source.load()
                    clean = ImageOps.exif_transpose(source).convert('RGBA')
                    clean.thumbnail((1600, 1600))
                    output = BytesIO()
                    clean.save(output, format='PNG', optimize=True)
        except (OSError, UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
            raise ValueError('Image invalide ou trop volumineuse.') from exc
        self.image_dir.mkdir(parents=True, exist_ok=True)
        target = self.image_dir / f'{uuid4().hex}.png'
        try:
            with target.open('xb') as file:
                file.write(output.getvalue())
            product.image_path = str(target)
            self.db.commit()
        except Exception:
            self.db.rollback()
            target.unlink(missing_ok=True)
            raise
        return target

    def remove(self, product_id):
        product = self.db.get(Product, product_id)
        if not product:
            raise ValueError('Produit introuvable.')
        product.image_path = None
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        # On ne supprime pas les fichiers : une ancienne sauvegarde peut les référencer.

    def safe_path(self, product):
        if not product.image_path:
            return None
        root = self.image_dir.resolve()
        path = Path(product.image_path).resolve()
        if path.parent != root or path.suffix.lower() != '.png' or not path.is_file():
            return None
        return path
