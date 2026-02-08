SELECT A.*, B.new_value FROM "{file}" AS A
LEFT JOIN "{another_file}" AS B
  USING (key);
