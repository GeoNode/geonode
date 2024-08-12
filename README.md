# DCS Data Catalog

docker compose -f docker-compose-dev.yml build --no-cache
docker compose -f docker-compose-dev.yml up -d

## NOTES

- admin selection staff member icin gorulmuyor. onu kontrol edip eger kullanici staff sa onu gosterelim

2 tane post endpoint senaryomuz var
1- rating   >> sadece rating olursa geometrisini backend olusturalim. 
2- rating feat feedback form

- endate bugun olmamali. bundan buyuk olmali.
- enddate i bugunden buyuk olanlari doneceez. start_date de bugun yada bugunden kucukleri donmek lazim. 
- active diye bir default column ekleyip endate de sonra deactive yapabiliriz.
- campaign de enddate dolduysa hata donmek lazim. nice to have