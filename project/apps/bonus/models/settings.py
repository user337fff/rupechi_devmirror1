from django.db import models


class BonusSettings(models.Model):
    class Meta:
        verbose_name = 'Настройки бонусной системы'
        verbose_name_plural = 'Настройки бонусной системы'

    order_deposit_percent = models.PositiveIntegerField(
        verbose_name='Бонусов за заказ в %', default=0)
    order_withdraw_percent = models.PositiveIntegerField(
        verbose_name='Максимальное списание бонусов от заказа в %', default=0)
    lifetime_bonuses = models.PositiveIntegerField(
        verbose_name='Дней до сгорания бонусов', default=0,
        help_text='Если бонусы бессрочные, то оставить равным нулю')

    register_bonuses = models.PositiveIntegerField(
        verbose_name='Бонусов за регистрацию', default=0)
    register_lifetime_bonuses = models.PositiveIntegerField(
        verbose_name='Дней до сгорания регистрационных бонусов', default=0,
        help_text='Если бонусы бессрочные, то оставить равным нулю')

    first_order_bonuses = models.PositiveIntegerField(
        verbose_name='Бонусов за первый заказ', default=0)
    first_order_lifetime_bonuses = models.PositiveIntegerField(
        verbose_name='Дней до сгорания бонусов за первый заказ', default=0,
        help_text='Если бонусы бессрочные, то оставить равным нулю')

    def __str__(self):
        return 'Настройки бонусной системы'

    def save(self, *args, **kwargs):
        self.__class__.objects.exclude(id=self.id).delete()
        super(BonusSettings, self).save(*args, **kwargs)

    @classmethod
    def load(cls):
        try:
            return cls.objects.get()
        except cls.DoesNotExist:
            return cls()
