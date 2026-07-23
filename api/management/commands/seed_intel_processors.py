from django.core.management.base import BaseCommand
from api.models import Procesador

class Command(BaseCommand):
    help = "Seeds Intel processors from 8th Generation onwards into the catalog"

    def handle(self, *args, **options):
        processors = [
            # 8th Generation
            "Intel Core i3-8100",
            "Intel Core i5-8250U",
            "Intel Core i5-8350U",
            "Intel Core i5-8400",
            "Intel Core i5-8500",
            "Intel Core i7-8550U",
            "Intel Core i7-8650U",
            "Intel Core i7-8700",
            "Intel Core i7-8750H",
            "Intel Core i9-8950HK",

            # 9th Generation
            "Intel Core i3-9100",
            "Intel Core i5-9300H",
            "Intel Core i5-9400",
            "Intel Core i7-9700",
            "Intel Core i7-9750H",
            "Intel Core i9-9900K",

            # 10th Generation
            "Intel Core i3-10110U",
            "Intel Core i5-10210U",
            "Intel Core i5-1035G1",
            "Intel Core i5-10400",
            "Intel Core i7-10510U",
            "Intel Core i7-1065G7",
            "Intel Core i7-10750H",
            "Intel Core i7-10700",
            "Intel Core i9-10900K",

            # 11th Generation
            "Intel Core i3-1115G4",
            "Intel Core i5-1135G7",
            "Intel Core i5-1145G7",
            "Intel Core i5-11400",
            "Intel Core i7-1165G7",
            "Intel Core i7-1185G7",
            "Intel Core i7-11800H",
            "Intel Core i9-11900K",

            # 12th Generation
            "Intel Core i3-1215U",
            "Intel Core i5-1235U",
            "Intel Core i5-1240P",
            "Intel Core i5-12450H",
            "Intel Core i5-12500H",
            "Intel Core i5-12400",
            "Intel Core i7-1255U",
            "Intel Core i7-1260P",
            "Intel Core i7-12700H",
            "Intel Core i7-12700",
            "Intel Core i9-12900H",
            "Intel Core i9-12900K",

            # 13th Generation
            "Intel Core i3-1315U",
            "Intel Core i5-1335U",
            "Intel Core i5-1340P",
            "Intel Core i5-13420H",
            "Intel Core i5-13500H",
            "Intel Core i5-13400",
            "Intel Core i7-1355U",
            "Intel Core i7-1360P",
            "Intel Core i7-13700H",
            "Intel Core i7-13700",
            "Intel Core i9-13900H",
            "Intel Core i9-13900K",

            # 14th Generation / Raptor Lake Refresh
            "Intel Core i5-14400",
            "Intel Core i7-14700",
            "Intel Core i7-14700HX",
            "Intel Core i9-14900K",
            "Intel Core i9-14900HX",

            # Intel Core Ultra (Series 1 & 2)
            "Intel Core Ultra 5 125U",
            "Intel Core Ultra 5 125H",
            "Intel Core Ultra 7 155U",
            "Intel Core Ultra 7 155H",
            "Intel Core Ultra 9 185H",
            "Intel Core Ultra 5 226V",
            "Intel Core Ultra 7 258V"
        ]

        created_count = 0
        for name in processors:
            obj, created = Procesador.objects.get_or_create(nombre=name)
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {created_count} new Intel processors (8th Gen+)."))
