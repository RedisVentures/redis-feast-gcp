# Create an ENV file

touch .env

while read p; do
  echo $p
  read -u 1 input
  echo $p$input >> .env
done <.env.template