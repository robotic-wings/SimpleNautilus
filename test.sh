#!/bin/bash

coverage erase
for testcase in pwd_trivial sweet_home weirdo perm
do
  coverage run -a nautilus.py < e2e_tests/$testcase.in | diff e2e_tests/$testcase.out - > e2e_tests/$testcase\_actual.out
  char_count=$(cat e2e_tests/$testcase\_actual.out | wc -c)
  if [ $char_count -eq 0 ]
  then
    echo "Testcase $testcase passed!"
  else
    echo "Did not pass testcase $testcase"
    cat e2e_tests/$testcase\_actual.out
  fi
done
coverage report
