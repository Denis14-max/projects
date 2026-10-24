from django.db import models


class Category(models.Model):
    title = models.CharField(max_length=150, verbose_name="Название")
    image = models.FileField(upload_to="categories/icons/", null=True, blank=True, verbose_name="Иконка")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name="subcategories",
                               verbose_name="Родительская категория")
    is_deleted = models.BooleanField(default=False, verbose_name="Удалена")

    def soft_delete(self):
        self.is_deleted = True
        self.save()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"


class Tag(models.Model):
    """Модель тегов для товаров"""
    name = models.CharField(max_length=50, verbose_name="Название тега")

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products", verbose_name="Категории")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Цена")
    count = models.PositiveIntegerField(default=0, verbose_name="Количество")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Краткое описание")
    fullDescription = models.TextField(blank=True, verbose_name="Полное описание")
    freeDelivery = models.BooleanField(default=False, verbose_name="Бесплатная доставка")

    is_limited = models.BooleanField(default=False, verbose_name="Ограниченный тираж")
    sort_index = models.IntegerField(default=0, verbose_name="Индекс сортировки")
    purchases = models.IntegerField(default=0, verbose_name="Количество покупок")

    is_deleted = models.BooleanField(default=False, verbose_name="Удален")
    tags = models.ManyToManyField(Tag, related_name="products", verbose_name="Теги", blank=True)

    def soft_delete(self):
        self.is_deleted = True
        self.save()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images", verbose_name="Товар")
    image = models.ImageField(upload_to="products/images/", verbose_name="Изображение")

    class Meta:
        verbose_name = "Изображение товара"
        verbose_name_plural = "Изображения товара"


class Specification(models.Model):
    """Характеристики товара"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='specifications', verbose_name="Товар")
    name = models.CharField(max_length=100, verbose_name="Имя характеристики")
    value = models.CharField(max_length=100, verbose_name="Значение")

    class Meta:
        verbose_name = "Характеристика"
        verbose_name_plural = "Характеристики"

    def __str__(self) -> str:
        return f"{self.name}: {self.value}"


class Review(models.Model):
    """Отзывы к товарам"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name="Товар")
    author = models.CharField(max_length=150, verbose_name="Автор")
    email = models.EmailField(verbose_name="Email")
    text = models.TextField(verbose_name="Текст отзыва")
    rate = models.PositiveSmallIntegerField(verbose_name="Оценка", default=5)
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"

    def __str__(self) -> str:
        return f"Отзыв от {self.author} на {self.product.title}"
